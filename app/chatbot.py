from __future__ import annotations

import re
from typing import List, Sequence

from app.config import settings
# Note: is_food_image is kept for backward compatibility but validation is now combined with analysis
# from app.image_validator import is_food_image
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

    def is_food_related(self, query: str, history: Sequence[dict] | None = None) -> bool:
        """
        Check if query is related to food/cooking topics.
        
        Args:
            query: The user's question or message
            history: Optional conversation history to check for context (e.g., recent image analysis)
        
        Returns:
            True if the query is food-related, False otherwise
        """
        # Normalize query: remove punctuation and extra spaces for better matching
        query_normalized = re.sub(r'[^\w\s]', '', query.lower())
        query_normalized = ' '.join(query_normalized.split())
        # Check if any keyword appears in the normalized query
        if any(keyword in query_normalized for keyword in self.FOOD_KEYWORDS):
            return True
        
        # Check if this is a follow-up to image analysis
        # If history exists and contains recent image analysis, treat follow-up questions as food-related
        if history:
            # Check only the most recent 2 turns to see if there was an image analysis
            # This ensures immediate follow-up questions after image uploads are treated as food-related
            # but prevents old image analyses from affecting unrelated questions
            for turn in reversed(history[-2:]):  # Check most recent 2 turns only
                if turn.get('user', '').startswith('[IMAGE]'):
                    # This is a follow-up to image analysis - treat as food-related
                    return True
        
        return False

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

    def answer(self, question: str, history: Sequence[dict] | None = None, user_id: str | None = None, conversation_id: str | None = None) -> str:
        is_food_related = self.is_food_related(question, history=history)
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
                answer = llm_client.chat(messages, timeout=settings.llm_timeout_seconds)
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
                answer = llm_client.chat(messages, timeout=settings.llm_timeout_seconds)
            
            # Log the conversation
            conversation_logger.log_conversation(
                question=question,
                answer=answer,
                is_food_related=is_food_related,
                num_retrieved_docs=num_retrieved_docs,
                history_length=history_length,
                user_id=user_id,
                conversation_id=conversation_id,
                metadata={
                    "model": settings.llm_model,
                    "temperature": settings.temperature,
                },
            )
            
            return answer
            
        except TimeoutError as e:
            # Log timeout errors with context
            conversation_logger.log_error(
                e,
                context={
                    "question": question,
                    "is_food_related": is_food_related,
                    "history_length": history_length,
                    "user_id": user_id,
                    "error_type": "timeout",
                },
            )
            # Re-raise with user-friendly message
            raise TimeoutError(
                f"The request took too long to process. Please try again with a simpler question or check your connection."
            ) from e
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
        history: Sequence[dict] | None = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
        image_url: str | None = None,
    ) -> str:
        """
        Analyze an image and answer questions about it.
        
        Optimization: Validation is combined with analysis in a single API call for faster processing.
        The prompt includes a validation check that returns "NOT_FOOD" if the image is not food-related.
        
        Args:
            image_data: Image data (bytes or file path)
            question: Question about the image
            history: Optional conversation history to provide context for follow-up questions
            user_id: Optional user identifier
            conversation_id: Optional conversation identifier
        """
        try:
            # Encode image to base64 (with aggressive optimization: 1024x1024, quality 75)
            image_base64 = encode_image_to_base64(image_data)
            
            # Validation is now combined with analysis in a single API call for better performance
            # This eliminates the separate validation call, reducing processing time significantly
            
            # Determine which prompt to use based on question
            question_lower = question.lower()
            if "calorie" in question_lower or "calories" in question_lower:
                base_prompt = CALORIE_FOCUS_PROMPT
            else:
                base_prompt = IMAGE_ANALYSIS_PROMPT
            
            # Build the analysis prompt with conversation history if available
            if history and len(history) > 0:
                # Format history for inclusion in prompt
                history_text = "\n".join([
                    f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}"
                    for turn in history
                ])
                analysis_prompt = f"""{base_prompt}

<ConversationHistory>
{history_text}
</ConversationHistory>

IMPORTANT: This is a follow-up question in an ongoing conversation. Continue naturally and reference previous context when relevant. Do NOT repeat introductions or start from the beginning. If the user is asking about a previous image analysis, reference that analysis naturally.

User question: {question}"""
            else:
                analysis_prompt = f"{base_prompt}\n\nUser question: {question}"
            
            # Add language instruction to respond in the same language as the question
            analysis_prompt = f"{analysis_prompt}\n\nIMPORTANT: Respond in the same language as the user's question. If the question is in Arabic, respond in Arabic. If the question is in English, respond in English."
            
            # Analyze image (validation is combined in the prompt)
            answer = llm_client.analyze_image(image_base64, analysis_prompt, timeout=settings.vision_timeout_seconds)
            
            # Check if the response indicates the image is not food-related
            # The prompt instructs the model to return "NOT_FOOD" if the image is not food-related
            if answer.strip().upper() == "NOT_FOOD" or answer.strip().upper().startswith("NOT_FOOD"):
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
                metadata = {
                    "model": settings.vision_model,
                    "has_image": True,
                    "image_validated": False,
                    "validation_combined": True,
                }
                if image_url:
                    metadata["image_url"] = image_url
                
                conversation_logger.log_conversation(
                    question=f"[IMAGE] {question}",
                    answer=answer,
                    is_food_related=False,
                    num_retrieved_docs=0,
                    history_length=0,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    metadata=metadata,
                )
                return answer
            
            # Image is food-related - log the successful analysis
            history_length = len(history) if history else 0
            metadata = {
                "model": settings.vision_model,
                "has_image": True,
                "image_validated": True,
                "validation_combined": True,
            }
            if image_url:
                metadata["image_url"] = image_url
            
            conversation_logger.log_conversation(
                question=f"[IMAGE] {question}",
                answer=answer,
                is_food_related=True,
                num_retrieved_docs=0,
                history_length=history_length,
                user_id=user_id,
                conversation_id=conversation_id,
                metadata=metadata,
            )
            
            return answer
            
        except TimeoutError as e:
            # Log timeout errors with context
            conversation_logger.log_error(
                e,
                context={
                    "question": f"[IMAGE] {question}",
                    "is_food_related": True,
                    "user_id": user_id,
                    "has_image": True,
                    "error_type": "timeout",
                },
            )
            # Re-raise with user-friendly message
            raise TimeoutError(
                f"Image analysis took too long. Please try again with a smaller image or a simpler question."
            ) from e
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
