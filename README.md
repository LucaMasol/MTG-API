# TODO: OUT OF DATE

# MTG Meta Analytics API
An API for analysing the Magic: The Gathering Pauper archetypal metagame over time, comparitively with user-inputted decks.

## Project overview
* Users can authenticate via a basic signup process, accepting an email and password. An API key is generated from this that the user can utilise for future requests. All other routes will require this API key, or not accept the request.
* The user can query endpoints to receive data of trends in the Pauper archetypal metagame in the form of JSON, or, for demonstrative purposes, visualisations of said data.
* The user can create their own decks and decklists. These decklists can be estimated to fall under an archetype, and the user can test how 'spicy' (non-conforming) their list is compared to the recent well-performing meta.


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
### Prerequisites
* Docker
* Spicerack.gg API key
  1. First, create a user account (https://www.spicerack.gg/)
  2. Second, create an organisational account (https://docs.spicerack.gg/)
  3. Go to the admin dashboard and then to the organisation settings. Here, you can find your API key

### Environment
1. Create a `.env` file given the structure of `./.env.example`.
2. Add your Spicerack API key to the `.env` file. If you do not have one, you will need to set up an account.

### Installation
1. Clone the repository via `git clone` or downloading the repo as a .zip file.
2. Ensure the Docker engine is running
3. Run `docker compose up --build`
    * The first time this run, the database is created and filled, and will take a significant amount of time, of at least 40 minutes. Rate limiters are being used as to not over-request Moxfield's API.
4. To run in the future, run `docker compose up --build` again.

### Data Import/ Preprocessing Pipeline TODO - more detail
The following pipeline is initiated at a time of 240 days when the server first opens. This will take upwards of 40 minutes on its first run. While the server is running, every 6 hours, the pipeline is run again for the period of 2 days. This is to ensure any recently ended events are not omitted from the dataset, and the database remains up-to-date.
1. Import Tournament Data
Fetches tournament data and results using the Spicerack API and stores in the database

2. Fetch Decklists
For each deck that has not been processed, gets the decklists for the deck using Moxfield's API and stores it in the database.
Will take a good amount of time, but can be cancelled and continued at a later point.

3. Archetype Classification
Classifies the archetype for all unclassified decks using core cards in the archetypes

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

## Data Sources
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