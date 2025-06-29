from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os
from pypdf import PdfReader



def return_keywords(cv_pdf_path: str, llm_model: str = "gemma3:1b") -> str:
    """
    Function to return keywords from a CV PDF file.
    :param cv_pdf_path: Path to the CV PDF file.
    :param llm_model: The language model to use for processing.
    :return: A string containing the keywords extracted from the CV.
    """
    # creating a pdf reader object
    reader = PdfReader(cv_pdf_path)

    # Create the ChatOllama model
    model = ChatOllama(model=llm_model)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    sys = SystemMessage(f"""You are my assistant. The following text is a CV  \n {text}. \n
          I will require some help""")


    messages = [
        sys,
        HumanMessage("Please give me 4 keywords to search in a job application portal for this CV. Please only return the 4 keywords, separated by a comma.")
    ]

    result = model.invoke(messages)

    return result.content



if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    cv_pdf_path = os.path.join(path,"Test_CV" ,"skills-based-cv.pdf")
    llm_model = "gemma3:1b"
    keywords = return_keywords(cv_pdf_path, llm_model)
    print(f"Keywords extracted from CV: {keywords}")