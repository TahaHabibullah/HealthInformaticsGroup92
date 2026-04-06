from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import json

class ClinicalRetrieval:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.cases = []
        self.case_texts = []
        self.embeddings = None

    def load_dataset(self):
        dataset = load_dataset("AGBonnet/augmented-clinical-notes", split="train[:5000]")

        self.cases = [dict(item) for item in dataset]

        self.case_texts = []
        for case in self.cases:
            visit_motivation = case.get("visit motivation", "")
            symptoms = case.get("symptoms", [])
            symptom_text = " ".join(
                symptom.get("name of symptom", "")
                for symptom in symptoms
                if isinstance(symptom, dict)
            )

            combined_text = f"{visit_motivation} {symptom_text}".strip()

            if not combined_text:
                combined_text = json.dumps(case)

            self.case_texts.append(combined_text)

        print(f"Loaded {len(self.cases)} clinical notes")

    def build_index(self):
        print("Generating embeddings...")
        self.embeddings = self.model.encode(self.case_texts, show_progress_bar=True)

        with open("embeddings.pkl", "wb") as f:
            pickle.dump((self.cases, self.case_texts, self.embeddings), f)

        print("Index saved locally")

    def load_index(self):
        with open("embeddings.pkl", "rb") as f:
            self.cases, self.case_texts, self.embeddings = pickle.load(f)

    def _build_case_summary(self, case_data):
        patient_info = case_data.get("patient information", {})
        visit_motivation = case_data.get("visit motivation", "No visit motivation listed")
        symptoms = case_data.get("symptoms", [])
        diagnosis_tests = case_data.get("diagnosis tests", [])

        age = patient_info.get("age", "Unknown")
        sex = patient_info.get("sex", "patient")

        symptom_names = []
        for symptom in symptoms[:3]:
            if isinstance(symptom, dict):
                name = symptom.get("name of symptom")
                if name and name != "None":
                    symptom_names.append(name)

        diagnosis_result = None
        for test in diagnosis_tests:
            if isinstance(test, dict):
                condition = test.get("condition")
                result = test.get("result")
                if condition and condition != "None":
                    diagnosis_result = condition
                    break
                if result and result != "None":
                    diagnosis_result = result
                    break

        summary = f"{age}-year-old {str(sex).lower()} presented with {str(visit_motivation).lower()}."

        if symptom_names:
            summary += " Main symptoms included " + ", ".join(symptom_names).lower() + "."

        if diagnosis_result:
            summary += f" Key finding: {diagnosis_result}."

        return summary

    def query(self, symptoms, top_k=5):
        query_embedding = self.model.encode([symptoms])[0]

        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for i in top_indices:
            case_data = self.cases[i]
            results.append({
                "summary": self._build_case_summary(case_data),
                "full_case": json.dumps(case_data, indent=2)
            })

        return results


if __name__ == "__main__":
    retriever = ClinicalRetrieval()
    retriever.load_dataset()
    retriever.build_index()

    results = retriever.query("chest pain and shortness of breath")
    for i, result in enumerate(results, start=1):
        print(f"\nResult {i} Summary: {result['summary']}")
        print(result["full_case"])