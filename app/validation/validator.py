from app.models.models import *
from fastapi import UploadFile
from tinydb import TinyDB, Query
from app.models.pyrodb import *

poke_db = TinyDB("./app/database/pokemons.json", indent = 4)
stone_db = TinyDB("./app/database/stones.json", indent = 4)
tm_db = TinyDB("./app/database/tms.json", indent = 4)
balls_db = TinyDB("./app/database/pokeballs.json", indent = 4)

query = Query()

class Validate():
    
    def credential_length(self, credential: str, max_lenght: int = 100, min_lenght: int = 2) -> bool:
        
        if len(credential) > max_lenght:
            return False
        
        if len(credential) < min_lenght:
            return False
        
        return True
    
    def username(self, username: str):
        max_lenght = 25
        min_lenght = 3

        if not username.isalnum():
            print(username, username.isalnum())
            return "Username can only have Letters and Numbers"
        
        elif not self.credential_length(username, max_lenght, min_lenght):
            return "Username must have between 3 and 25 characters"
        
        return False

    def email(self, email: str):
        invalid_chars = r'\#!$%¨&*()-=+[{]}|'
        max_lenght = 50
        min_lenght = 5

        if not email.replace("@", "").replace(".", "").isalnum():
            return "Email contains illegal characters"
        
        elif any(c in invalid_chars for c in email):
            return "Email contains illegal characters"
        
        elif not self.credential_length(email, max_lenght, min_lenght):
            return "Email must have between 5 and 50 characters"
        
        return False
    

    def password(self, password: str):
        max_lenght = 32
        min_lenght = 8

        if not password.isascii():
            return "Password contains illegal characters"
        
        elif not self.credential_length(password, max_lenght, min_lenght):
            return "Password must have between 8 and 32 characters"
        
        return False
    
    def post(self, post: Post):

        post = post.model_dump()

        # --> Title
        post_title = post["title"]

        if not self.credential_length(post_title, 25):
            return "Post title must have between 2 and 25 characters"
    
        # --> Description
        post_description = post["description"]

        if not self.credential_length(post_description, 1000):
            return "Post description must have between 2 and 1000 characters"
        
        return False
    
    def validate_pokemon(self, pokemon: Pokemon):
        pokemon_data = pokemon.model_dump()

        # Validate name
        if not poke_db.search(query.name == pokemon_data['name']):
            return "Invalid pokemon name"

        # Validate level
        if not (1 <= pokemon_data['level'] <= 100):
            return "Pokemon level must be between 1 and 100"

        # Validate nature
        if not self.credential_length(pokemon_data['nature'], 20):
            return "Pokemon nature must have between 2 and 20 characters"

        # Validate pokeball
        if not self.credential_length(pokemon_data['pokeball'], 20):
            return "Pokemon pokeball must have between 2 and 20 characters"

        # Validate addon
        if not self.credential_length(pokemon_data['addon'], 100, 0):
            return "Pokemon addon must have a maximum of 100 characters" 

        # Validate boost
        if not (0 <= pokemon_data['boost'] <= 10):
            return "Pokemon boost must be between 0 and 10" 

    def validate_items(self, item: Item):
        item_data = item.model_dump()

        types = ["stone", "tm", "pokeball", "undefined"]

        if not item_data['type'] in types:
            return "Item don't have a specific type"
        
        if item_data['type'] == 'stone':
            if not stone_db.search(query.name == item_data['name']):
                return "Invalid stone name." 
        elif item_data['type'] == 'tm':
            if not tm_db.search(query.name == item_data['name']):
                return "Invalid TM name."
        elif item_data['type'] == 'pokeball':
            if not balls_db.search(query.name == item_data['name']):
                return "Invalid pokeBall name." 
        elif item_data['type'] == 'undefined':
            if not self.credential_length(item_data['name'], 50):
                return "Item type must have between 2 and 50 characters." 

        # Validate type
        if not self.credential_length(item_data['type'], 50):
            return "Item type must have between 2 and 50 characters"

        # Validate name
        if not self.credential_length(item_data['name'], 50):
            return "Item name must have between 2 and 50 characters" 
    
    def validate_post(self, post_identifier: str, user: User):
        
        user_data = user.model_dump()
        if not post_identifier in user_data['posts']:
            return "You don't have access to this post"

    