# Talk2Paperless

This is a FastAPI application that acts as an API for a natural language chatbot that interacts with a [Paperless-ngx](https://paperless-ngx.com/) instance. The API parses user queries to extract relevant information (like document types, dates, and names), searches for documents in Paperless-ngx, and returns a formatted, user-friendly response with links to the found documents.

### Features

* **Natural Language Processing:** Uses `spaCy` to parse German text queries and identify key entities.

* **Intelligent Search:** Extracts document types, tags, contributors, and dates from queries to build a comprehensive search request for Paperless-ngx.

* **Dynamic Pagination:** Fetches all matching documents from the Paperless-ngx API, handling pagination automatically.

* **User-Friendly Output:** Formats the search results into a clean, readable message with direct links to the documents in the Paperless-ngx web interface.

* **Robust Error Handling:** Includes basic error handling for API requests and JSON parsing.

### Prerequisites

Before running the application, ensure you have the following installed:

* Python 3.7+

* An active Paperless-ngx instance.
