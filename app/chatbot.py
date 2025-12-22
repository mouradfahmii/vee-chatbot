from __future__ import annotations

import re
from typing import List, Sequence

from app.config import settings
from app.image_validator import is_food_image
from app.image_utils import encode_image_to_base64
from app.llm import llm_client
from app.logger import conversation_logger
from app.prompts import CALORIE_FOCUS_PROMPT, CHAT_PROMPT_TEMPLATE, IMAGE_ANALYSIS_PROMPT, SYSTEM_PROMPT
from app.vector_store import Document, vector_store


class FoodChatbot:
    # Keywords that indicate food/cooking-related topics
    FOOD_KEYWORDS = {
        "cook", "recipe", "meal", "food", "dinner", "lunch", "breakfast", "snack",
        "ingredient", "calorie", "calories", "nutrition", "diet", "prep", "preparation",
        "kitchen", "bake", "roast", "grill", "fry", "steam", "boil", "sauté",
        "protein", "carb", "fat", "macro", "serving", "portion", "dietary",
        "allergy", "vegetarian", "vegan", "pescatarian", "gluten", "dairy",
        "session", "chef", "cooking class", "meal plan", "prep time", "cook time",
        "calculate", "track", "photo", "upload", "estimate"
    }

    def __init__(self) -> None:
        self.system_prompt = SYSTEM_PROMPT

    def contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        return bool(arabic_pattern.search(text))

    def is_food_related(self, query: str) -> bool:
        """Check if query is related to food/cooking topics."""
        # Normalize query: remove punctuation and extra spaces for better matching
        query_normalized = re.sub(r'[^\w\s]', '', query.lower())
        query_normalized = ' '.join(query_normalized.split())
        # Check if any keyword appears in the normalized query
        return any(keyword in query_normalized for keyword in self.FOOD_KEYWORDS)

    def build_context(self, query: str) -> List[Document]:
        return vector_store.query(query, n_results=settings.max_context_documents)

    def format_history(self, history: Sequence[dict] | None) -> str:
        if not history:
            return "(none)"
        formatted = []
        for turn in history:
            formatted.append(f"User: {turn['user']}")
            formatted.append(f"Assistant: {turn['assistant']}")
        return "\n".join(formatted)

    def format_context(self, docs: Sequence[Document]) -> str:
        if not docs:
            return "No matching knowledge found."
        chunks = []
        for doc in docs:
            prefix = doc.metadata.get("type", "doc")
            chunks.append(f"[{prefix}:{doc.doc_id}] {doc.content}")
        return "\n".join(chunks)
    
    def has_relevant_context(self, docs: Sequence[Document]) -> bool:
        """
        Check if retrieved documents contain relevant context.
        Returns True if context exists and appears relevant, False otherwise.
        """
        if not docs or len(docs) == 0:
            return False
        # If we have documents, consider them relevant
        # The vector store should already filter by relevance
        return True

    def build_prompt(self, question: str, history: Sequence[dict] | None, docs: Sequence[Document]) -> str:
        return CHAT_PROMPT_TEMPLATE.format(
            system_prompt=self.system_prompt,
            history=self.format_history(history),
            context=self.format_context(docs),
            question=question,
        )

    def answer(self, question: str, history: Sequence[dict] | None = None, user_id: str | None = None) -> str:
        is_food_related = self.is_food_related(question)
        history_length = len(history) if history else 0
        num_retrieved_docs = 0
        answer = ""
        
        try:
            # Quick scope check - if clearly not food-related, add explicit instruction
            if not is_food_related:
                # Let LLM handle it naturally but with context-aware redirect
                history_context = "There is conversation history, so do NOT repeat your introduction. Continue naturally." if history else "This is the first message, so you can introduce yourself if appropriate."
                prompt = (
                    f"User message: {question}\n\n"
                    f"This message does NOT appear to be about food, cooking, recipes, meals, or nutrition. "
                    f"{history_context} "
                    "Please acknowledge it naturally (if it's a greeting, acknowledge it; if it's a question, "
                    "politely decline) and redirect to food topics. Be contextual and friendly, but always redirect "
                    "to your role as a culinary assistant. If there's history, be conversational and don't repeat yourself."
                )
                messages = [
                    {"role": "system", "content": self.system_prompt},
                ]
                # Include history in messages for context
                if history:
                    for turn in history:
                        messages.append({"role": "user", "content": turn["user"]})
                        messages.append({"role": "assistant", "content": turn["assistant"]})
                messages.append({"role": "user", "content": prompt})
                answer = llm_client.chat(messages)
            else:
                # Always query knowledge base first for food-related questions
                docs = self.build_context(question)
                num_retrieved_docs = len(docs)
                has_kb_context = self.has_relevant_context(docs)
                
                # Build prompt with knowledge base context
                prompt = self.build_prompt(question, history, docs)
                
                # Add explicit instruction about knowledge base priority
                if has_kb_context:
                    prompt += "\n\nCRITICAL: You have RetrievedContext above. You MUST prioritize and use information from the RetrievedContext as your primary source. Only use general knowledge if the context doesn't fully answer the question."
                else:
                    prompt += "\n\nNOTE: No relevant knowledge base context was found. You may use your general culinary knowledge, but ONLY for food/cooking topics. Maintain strict scope."
                
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ]
                answer = llm_client.chat(messages)
            
            # Log the conversation
            conversation_logger.log_conversation(
                question=question,
                answer=answer,
                is_food_related=is_food_related,
                num_retrieved_docs=num_retrieved_docs,
                history_length=history_length,
                user_id=user_id,
                metadata={
                    "model": settings.llm_model,
                    "temperature": settings.temperature,
                },
            )
            
            return answer
            
        except Exception as e:
            # Log errors
            conversation_logger.log_error(
                e,
                context={
                    "question": question,
                    "is_food_related": is_food_related,
                    "history_length": history_length,
                    "user_id": user_id,
                },
            )
            raise

    def answer_with_image(
        self,
        image_data: str | bytes,
        question: str = "What is in this image? Estimate the calories.",
        user_id: str | None = None,
    ) -> str:
        """Analyze an image and answer questions about it."""
        try:
            # Encode image to base64
            image_base64 = encode_image_to_base64(image_data)
            
            # Validate image is food-related
            if not is_food_image(image_base64):
                # Respond in the same language as the question
                if self.contains_arabic(question):
                    answer = (
                        "أنا في، مساعدك الطهي. يمكنني فقط تحليل الصور المتعلقة بالطعام. "
                        "يرجى تحميل صورة لوجبة أو طعام أو محتوى متعلق بالطهي."
                    )
                else:
                    answer = (
                        "I'm Vee, your culinary assistant. I can only analyze food-related images. "
                        "Please upload an image of a meal, food, or cooking-related content."
                    )
                # Log the declined image
                conversation_logger.log_conversation(
                    question=f"[IMAGE] {question}",
                    answer=answer,
                    is_food_related=False,
                    num_retrieved_docs=0,
                    history_length=0,
                    user_id=user_id,
                    metadata={
                        "model": settings.vision_model,
                        "has_image": True,
                        "image_validated": False,
                    },
                )
                return answer
            
            # Determine which prompt to use based on question
            question_lower = question.lower()
            if "calorie" in question_lower or "calories" in question_lower:
                analysis_prompt = CALORIE_FOCUS_PROMPT
            else:
                analysis_prompt = f"{IMAGE_ANALYSIS_PROMPT}\n\nUser question: {question}"
            
            # Add language instruction to respond in the same language as the question
            analysis_prompt = f"{analysis_prompt}\n\nIMPORTANT: Respond in the same language as the user's question. If the question is in Arabic, respond in Arabic. If the question is in English, respond in English."
            
            # Analyze image
            answer = llm_client.analyze_image(image_base64, analysis_prompt)
            
            # Log the conversation
            conversation_logger.log_conversation(
                question=f"[IMAGE] {question}",
                answer=answer,
                is_food_related=True,
                num_retrieved_docs=0,
                history_length=0,
                user_id=user_id,
                metadata={
                    "model": settings.vision_model,
                    "has_image": True,
                    "image_validated": True,
                },
            )
            
            return answer
            
        except Exception as e:
            conversation_logger.log_error(
                e,
                context={
                    "question": f"[IMAGE] {question}",
                    "is_food_related": True,
                    "user_id": user_id,
                    "has_image": True,
                },
            )
            raise


bot = FoodChatbot()
