from __future__ import annotations

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

    def is_food_related(self, query: str) -> bool:
        """Check if query is related to food/cooking topics."""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.FOOD_KEYWORDS)

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
                # Still let LLM handle it with strict instructions, but add extra guard
                prompt = (
                    f"User question: {question}\n\n"
                    "IMPORTANT: This question does NOT appear to be about food, cooking, recipes, "
                    "meals, or nutrition. You MUST politely decline and redirect to food topics only. "
                    "Do NOT answer the question if it's not food-related."
                )
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ]
                answer = llm_client.chat(messages)
            else:
                docs = self.build_context(question)
                num_retrieved_docs = len(docs)
                prompt = self.build_prompt(question, history, docs)
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
