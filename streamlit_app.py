import streamlit as st
from database_query import DatabaseQuery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "query_handler" not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        db_path = os.getenv("DB_PATH", "chinook.db")  # fallback to chinook.db if not specified
        if not api_key:
            st.error("OpenAI API key not found in environment variables!")
            st.stop()
        st.session_state.query_handler = DatabaseQuery(db_path, api_key)

def main():
    st.set_page_config(
        page_title="SQL Query Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("SQL Query Assistant 🤖")
    
    # Initialize session
    init_session_state()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sql" in message:
                st.code(message["sql"], language="sql")
            if "results" in message and message["results"]:
                st.dataframe(message["results"])
            if "insights" in message:
                st.write("Insights:")
                st.write(message["insights"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            try:
                # Generate SQL
                sql_query = st.session_state.query_handler.generate_sql_query(prompt)
                st.write("Generated SQL:")
                st.code(sql_query, language="sql")
                
                # Execute query
                columns, results = st.session_state.query_handler.execute_query(sql_query)
                
                if results:
                    st.write("Results:")
                    st.dataframe(results)
                    
                    # Generate insights
                    insights = st.session_state.query_handler.generate_insights(
                        f"Analyze these query results for '{prompt}': {results}"
                    )
                    st.write("Insights:")
                    st.write(insights)
                    
                    # Add to message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Here's what I found:",
                        "sql": sql_query,
                        "results": results,
                        "insights": insights
                    })
                else:
                    st.write("No results found.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()