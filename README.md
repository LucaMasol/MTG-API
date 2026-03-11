# MTG Meta Analytics API

ToDo: short description

## Project overview
Todo: what the system does

## Architecture / Tech Stack
### Backend Framework
* FastAPI – Python API framework

### Database
* PostgreSQL – relational database for structured tournament and deck data
* SQLAlchemy – ORM used for database interaction

### External APIs / Sources
* Spicerack API – tournament data source
* Moxfield API – decklist retrieval

### Supporting Libraries
* httpx – HTTP requests to external APIs
* curl-cffi – requests for Moxfield API requests
* python-dotenv – environment variable management



## Setup Instructions
### Installation
1. Clone the repository via `git clone` or downloading the repo as a .zip file.
2. Create a Python virtual environment in the root of the project `python -m venv venv`
3. Activate the environment (differs per OS)
    * Windows: `venv\Scripts\activate`
    * Linux: `source venv/bin/activate`
4. Install npm dependencies: `pip install -r requirements.txt`

### Environment
1. Create a `.env` file given the structure of `./.env.example`.
2. Add your Spicerack API key to the `.env` file. If you do not have one, you will need to set up an account.

### Database setup
Ensure PostgreSQL is running and create the database with `createdb mtg_api_db`.
The database's tables will be created automatically when the import scripts are run.

### Data Import Pipeline
1. Import Tournament Data
Fetches tournament data and results using the Spicerack API and stores in the database
Run `python -m scripts.import_pauper_tournaments`

2. Fetch Decklists
For each deck that has not been processed, gets the decklists for the deck using Moxfield's API and stores it in the database.
Will take a good amount of time, but can be cancelled and continued at a later point.
Run `python -m scripts.process_moxfield_decklists`

3. Archetype Classification
Classifies the archetype for all unclassified decks using core cards in the archetypes
Run `python -m scripts.classify_decks`

## Database Schema
### Tournament
Stores metadata about each tournament.
One tournament has many decks.

### Deck
Stores individual deck results from each tournament.
One deck has one tournament and many decklist cards.

### Card
Stores unique card names.
One card has many instances in decklist cards.

### DecklistCard
Represents the many-to-many relationship between decks and cards, including quantities in mainboard and sideboard.
One decklist card has one deck and one card..

## API Documentation
Interactive API documentation is available at:
http://127.0.0.1:8000/docs

## 13. Data Sources
* Spicerack API – provides tournament results and deck metadata used to populate the database.
Spicerack. (2025). Spicerack API. Available at: https://api.spicerack.gg

* Moxfield API – used to retrieve full decklists for each deck entry.
Moxfield. (2025). Moxfield Deck API. Available at:https://api.moxfield.com

## Use of Generative AI
Generative AI tools were used during the development of this project as per the coursework specification.
Generative AI was used for:
* debugging Python code and resolving runtime errors
* exploring alternative architectural approaches
* improving code structure and refactoring
* discussing algorithmic approaches for deck classification options
* proof reading and structuring of README file
* initial list of core archetype cards, which was proof-read and cleaned

The primary AI tool used was:
* OpenAI ChatGPT (GPT-5) – OpenAI. (2025). ChatGPT Large Language Model. Available at https://chat.openai.com/

## References

Spicerack. (2025). *Spicerack API*. https://api.spicerack.gg

Moxfield. (2025). *Moxfield Deck API*. https://api.moxfield.com

OpenAI. (2025). *ChatGPT Large Language Model*. https://chat.openai.com