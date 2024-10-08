from django.shortcuts import render
from django.http import JsonResponse
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
assistant_id = os.getenv("ASSISTANT_ID")
thread = client.beta.threads.create()
thread_id = thread.id


def ask_assistant(user_input, pdf_context):

    # Add the user message to the Thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input+". The answer has to be based only on the file "+pdf_context+" stored on the vector store.",
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=assistant_id
    )

    messages = list(
        client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id)
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)

    message_content = messages.data[0].content[0].text

    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(
            annotation.text, f"[{index}]"
        )
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    return message_content.value, "\n".join(citations)

def chatbot(request):
    if request.method =="POST":
        pdf_context=request.POST.get('pdf_context')
        message = request.POST.get('message')
        response = ask_assistant(message,pdf_context)
        print(pdf_context)
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')
