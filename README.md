# Backend
This functions as the API connecting our project. Data in the database is synced from the blockchain when companies deem the product as ready for client facing. Not all blockchain infomration is available through the API, companies should request a blockchain wallet for direct access. 

![alt text](https://github.com/Green-Planet-Trust/Backend/blob/development/splash.png?raw=true)

# What I did to set up my enviornment 
0. *may not need* Set up Homebrew 
1. *may not need* `brew install python`
2. `sudo easy_install pip`
3. `sudo pip install pipenv`
    1. *only if command gave an error* `sudo -H pip install -U pipenv`
4. `pipenv install`
5. `pipenv run python server.py`

## NOTE
- The config files are stored in a config file kept offline since it has private keys, this is needed to run so just ask
- Also I removed a Python dependency in the Pipfile since it was not happy my version of python was ahead of the listed version (at least I hope so)

# Members
- Ariel Uy 
- Christopher Shortell
- Daniel Rodriguez 
- Jacob Engelbrecht 

# Purpose
This was built as part of the 2021 IBM Intern Hackathon!
