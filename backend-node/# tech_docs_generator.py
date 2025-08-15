# tech_docs_generator.py
import streamlit as st
import openai
import os
from datetime import datetime

# Configuration
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
DEFAULT_MODEL = "gpt-4"

# Documentation Templates
TEMPLATES = {
    "API Documentation": {
        "prompt": """Generate comprehensive {detail_level} OpenAPI documentation for:
Endpoint: {endpoint}
Method: {method}
Parameters: {params}
Request Body: {request_body}
Responses: {responses}
Target Audience: {audience}
Include {languages} code examples.""",
        "example": {
            "endpoint": "/api/v1/users",
            "method": "GET",
            "params": "limit: int, offset: int",
            "request_body": "None",
            "responses": "200: List of users, 401: Unauthorized",
            "languages": "Python and JavaScript",
            "audience": "Intermediate developers",
            "detail_level": "Detailed"
        }
    },
    "Code Documentation": {
        "prompt": """Document this {language} code for {audience} developers:
{code}
Include:
1. Function docstring in {style} format
2. Inline comments for complex logic
3. Usage examples
Detail Level: {detail_level}""",
        "example": {
            "language": "Python",
            "code": "def calculate_stats(data):\n    return {'mean': sum(data)/len(data), 'max': max(data)}",
            "style": "Google-style",
            "audience": "Beginner",
            "detail_level": "Standard"
        }
    },
    "Technical Tutorial": {
        "prompt": """Create a {detail_level} tutorial on {topic} for {audience}.
Include:
1. Prerequisites
2. Step-by-step instructions
3. Code examples in {language}
4. Common pitfalls
5. Further resources
Tone: {tone}""",
        "example": {
            "topic": "JWT Authentication in Flask",
            "audience": "Intermediate developers",
            "language": "Python",
            "tone": "Professional",
            "detail_level": "Detailed"
        }
    }
}

# Streamlit UI
st.set_page_config(page_title="TechDocs AI", layout="wide")
st.title("🤖 AI Technical Documentation Generator")

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    doc_type = st.selectbox("Document Type", list(TEMPLATES.keys()))
    model = st.selectbox("AI Model", ["gpt-4", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("Creativity", 0.0, 1.0, 0.3)
    
# Main Content
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Input Parameters")
    inputs = {}
    template = TEMPLATES[doc_type]
    
    # Show example button
    if st.button("Load Example"):
        for key, value in template["example"].items():
            inputs[key] = value
    
    # Dynamic form generation
    for field in template["prompt"].format(**template["example"]).split("{")[1:]:
        field_name = field.split("}")[0]
        if field_name not in inputs:
            if field_name == "code":
                inputs[field_name] = st.text_area("Code", height=200)
            elif field_name == "languages":
                inputs[field_name] = st.multiselect(
                    "Languages",
                    ["Python", "JavaScript", "Java", "Go", "C++"],
                    default=["Python", "JavaScript"]
                )
            elif field_name == "detail_level":
                inputs[field_name] = st.select_slider(
                    "Detail Level",
                    ["Brief", "Standard", "Detailed"]
                )
            elif field_name == "audience":
                inputs[field_name] = st.radio(
                    "Audience",
                    ["Beginner", "Intermediate", "Expert"]
                )
            else:
                inputs[field_name] = st.text_input(field_name.replace("_", " ").title())

with col2:
    st.subheader("Generated Documentation")
    if st.button("Generate Documentation"):
        try:
            # Build the prompt
            prompt = template["prompt"].format(**inputs)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            
            generated_content = response.choices[0].message.content
            st.session_state.generated_content = generated_content
            st.markdown(generated_content)
            
            # Add to history
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": doc_type,
                "content": generated_content[:100] + "..."
            })
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Show history if available
    if "history" in st.session_state and st.session_state.history:
        st.divider()
        st.subheader("History")
        for item in st.session_state.history:
            st.caption(f"{item['timestamp']} - {item['type']}")
            st.text(item["content"])

# Export Options
if "generated_content" in st.session_state:
    st.download_button(
        label="Download as Markdown",
        data=st.session_state.generated_content,
        file_name="documentation.md",
        mime="text/markdown"
    )