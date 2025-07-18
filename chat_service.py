from groq import Groq
import os

class ChatService:
    def __init__(self):
        # Initialize Groq client
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")  # Groq API key in .env file
        )
        self.model = "llama-3.1-8b-instant"  #  LLM model for querry response
        
    def generate_answer(self, question, context, source_url):
        """Generate answer based on context using Groq LLM"""
        try:
            prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from a specific document.


IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the information provided in the context below
2. If the context doesn't contain information to answer the question, say "I cannot find information about this in the provided document"
3. Do not use your general knowledge - stick strictly to the context
4. Be concise and accurate

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=500,
                temperature=0.1,  # Low temperature for more focused answers
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"Sorry, I encountered an error while generating the answer: {str(e)}"