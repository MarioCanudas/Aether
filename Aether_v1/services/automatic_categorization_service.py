import json
import os

from dotenv import load_dotenv
from models.transactions import Transaction
from openai import OpenAI


class AutomaticCategorizationService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_KEY")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def _prompt(self, content: str) -> str:
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": content},
            ],
            stream=False,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content
        assert isinstance(result, str), (
            f"The response content is not a string. content: {content}, response: {response}"
        )
        return result

    def categorize_transactions(
        self, transactions: list[Transaction], categories: list[str]
    ) -> dict[Transaction, str | None]:
        transactions_data = "\n".join(
            [
                t.model_dump_json(
                    include={"date", "amount", "description", "type", "statement_type"}
                )
                for t in transactions
            ]
        )

        categories_list = "\n".join(categories)

        prompt = f"""
            "Given the following categories:\n{categories_list}\n\n
            Categorize the following transactions:\n{transactions_data}\n\n
            Return a single JSON object with a key 'categories' which is a list of strings.
            Each string in the list should be the category for the corresponding transaction in the 
            same order. If you cannot determine a category for a transaction, use the JSON null 
            value for that entry.
        """
        response_str = self._prompt(prompt)

        try:
            # The model should return a JSON object like: {"categories": ["cat1", "cat2", ...]}
            data = json.loads(response_str)
            classifications = data.get("categories", [])

            return {t: c for t, c in zip(transactions, classifications, strict=True)}
        except json.JSONDecodeError:
            # Fallback or error handling if the response is not valid JSON
            return {t: None for t in transactions}
