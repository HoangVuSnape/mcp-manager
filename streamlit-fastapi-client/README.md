# Streamlit FastAPI Client

This project is a Streamlit application that interacts with a FastAPI server to retrieve and display server information.

## Project Structure

```
streamlit-fastapi-client
├── src
│   ├── app.py          # Main entry point for the Streamlit application
│   └── utils.py        # Utility functions for making HTTP requests
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Requirements

To run this project, you need to have Python installed along with the following packages:

- Streamlit
- httpx

You can install the required packages using the following command:

```
pip install -r requirements.txt
```

## Running the Application

1. Ensure that your FastAPI server is running on `localhost:3000`.
2. Navigate to the project directory in your terminal.
3. Run the Streamlit application with the following command:

```
streamlit run src/app.py
```

4. Open your web browser and go to `http://localhost:8501` to view the application.

## Usage

The application will automatically fetch the list of servers from the FastAPI server and display the results in the web interface.