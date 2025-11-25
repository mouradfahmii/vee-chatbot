from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from app.config import settings
from app.vector_store import Document, vector_store


class DatasetIngestor:
    """Transforms structured JSON data into retrieval-ready documents."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or settings.data_file

    def load_raw(self) -> Dict:
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_documents(self, payload: Dict) -> List[Document]:
        documents: List[Document] = []
        documents.extend(self._user_docs(payload.get("users", [])))
        documents.extend(self._meal_plan_docs(payload.get("mealPlans", [])))
        documents.extend(self._meal_docs(payload.get("meals", [])))
        documents.extend(self._session_docs(payload.get("sessions", [])))
        documents.extend(self._insight_docs(payload.get("calorieInsights", [])))
        documents.extend(self._photo_docs(payload.get("photoCalorieEstimates", [])))
        return documents

    def _user_docs(self, users: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for user in users:
            content = (
                f"User {user['name']} ({user['userId']}) goals: {', '.join(user['goals'])}. "
                f"Preferences: {', '.join(user['dietaryPreferences'])}. Allergies: {', '.join(user.get('allergies', []) or ['none'])}. "
                f"Active plan: {user['activePlanId']}. Sessions: {', '.join(user['sessionHistory'])}."
            )
            metadata = {
                "type": "user_profile",
                "userId": user["userId"],
                "timezone": user["timezone"],
            }
            docs.append(Document(doc_id=f"user::{user['userId']}", content=content, metadata=metadata))
        return docs

    def _meal_plan_docs(self, plans: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for plan in plans:
            content = (
                f"Meal plan {plan['name']} ({plan['planId']}) lasts {plan['durationWeeks']} weeks at {plan['dailyCalories']} kcal/day. "
                f"Macro split protein {plan['macros']['protein']}%, carbs {plan['macros']['carbs']}%, fat {plan['macros']['fat']}%. Focus: {plan['focus']}."
            )
            metadata = {
                "type": "meal_plan",
                "planId": plan["planId"],
                "scheduledMeals": ", ".join(plan["scheduledMeals"]),
            }
            docs.append(Document(doc_id=f"plan::{plan['planId']}", content=content, metadata=metadata))
        return docs

    def _meal_docs(self, meals: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for meal in meals:
            content = (
                f"Meal {meal['name']} ({meal['mealId']}) is a {meal['mealType']} for {meal['servings']} servings. "
                f"Prep {meal['prepTimeMinutes']} min, cook {meal['cookTimeMinutes']} min, {meal['calories']} kcal. "
                f"Ingredients: {', '.join(i['name'] for i in meal['ingredients'])}. "
                f"Nutrition -> protein {meal['nutrition']['protein']}g, carbs {meal['nutrition']['carbs']}g, fat {meal['nutrition']['fat']}g. "
                f"Suitable for {', '.join(meal['suitableFor'])}. Tags: {', '.join(meal['tags'])}."
            )
            metadata = {
                "type": "meal",
                "mealId": meal["mealId"],
                "mealType": meal["mealType"],
            }
            docs.append(Document(doc_id=f"meal::{meal['mealId']}", content=content, metadata=metadata))
        return docs

    def _session_docs(self, sessions: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for session in sessions:
            content = (
                f"Session {session['title']} ({session['sessionId']}) is a {session['type']} led by {session['coach']} on {session['scheduledDate']}. "
                f"Duration {session['durationMinutes']} minutes with {session['capacity']} seats ({session['booked']} booked). "
                f"Topics: {', '.join(session['topics'])}. Prep: {', '.join(session['requiredPrep'] or ['none'])}. Materials: {', '.join(session['materials'])}."
            )
            metadata = {
                "type": "session",
                "sessionId": session["sessionId"],
                "coach": session["coach"],
                "recordingAvailable": session["recordingAvailable"],
            }
            docs.append(Document(doc_id=f"session::{session['sessionId']}", content=content, metadata=metadata))
        return docs

    def _insight_docs(self, insights: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for insight in insights:
            content = (
                f"Calorie insight {insight['title']} ({insight['insightId']}) type {insight['type']} with data {insight['data']}. "
                f"Action: {insight['recommendedAction']}."
            )
            metadata = {
                "type": "insight",
                "insightId": insight["insightId"],
            }
            docs.append(Document(doc_id=f"insight::{insight['insightId']}", content=content, metadata=metadata))
        return docs

    def _photo_docs(self, photos: Iterable[Dict]) -> List[Document]:
        docs: List[Document] = []
        for photo in photos:
            content = (
                f"Photo calorie estimate {photo['photoId']} from user {photo['userId']} guesses {photo['mealGuess']} "
                f"at {photo['calorieEstimate']} kcal (confidence {photo['confidence']}). Ingredients: {', '.join(photo['detectedIngredients'])}."
            )
            metadata = {
                "type": "photo_estimate",
                "photoId": photo["photoId"],
                "userId": photo["userId"],
            }
            docs.append(Document(doc_id=f"photo::{photo['photoId']}", content=content, metadata=metadata))
        return docs

    def run(self, reset: bool = True) -> int:
        payload = self.load_raw()
        documents = self.build_documents(payload)
        if reset:
            vector_store.reset()
        vector_store.add(documents)
        return len(documents)


def ingest_dataset(reset: bool = True) -> int:
    return DatasetIngestor().run(reset=reset)
