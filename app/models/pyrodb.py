from decouple import config
from fastapi import HTTPException
from pymongo.mongo_client import MongoClient
from passlib.context import CryptContext
from app.models.models import *
from uuid import uuid4
from jose import jwt
from bson import ObjectId
from pymongo import MongoClient

# --> MongoDB Stuff <--
uri = config("URI_LINK")
db_con = MongoClient(uri)
db = db_con["PyroDB"]
users = db["Users"]
items = db["Items"]
pokemons = db["Pokemons"]
files = db["Files.files"]
posts = db["Posts"]


# --> Cache <--
cache_duration = float(config("CACHE_EXPIRE_MINUTES"))
cache = []


# --> Encryption <--
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# --> User Handling <--
def get_user(email: str):
    user = users.find_one({'email': email})
    if user:
        return UserInDB(**user)
    
def get_user_by_post(identifier: str) -> UserInDB:
    user: dict = users.find_one({'posts': [identifier]})
    if user:
        return UserProfile(username=user["username"], posts=user["posts"])
    return user

def add_user(username: str, email: str, password: str):
    hashed_password = get_password_hash(password)
    key = str(uuid4())
    user = UserInDB(username=username, email=email, key=key, hashed_password=hashed_password).model_dump()
    to_encode = {"email": email, "key": key}
    verification_code = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    if users.find_one({"email": user['email']}):
        return False
    users.insert_one(user)
    return verification_code

def append_post_to_owner(user_email: str, post_identifier: str):
    user = users.find_one({'email': user_email})
    if user:
        user_posts: list = user['posts']
        user_posts.append(post_identifier)
        users.update_one({'email': user_email}, {'$set': {'posts': user_posts}})
    else:
        raise HTTPException(400, "Couldn't append post to the user")
    
def verify_user(key) -> None:
    users.update_one({"key": key}, {"$set": {'isVerified': True}})


# --> Post Handling <--
def create_post(post: Post, user_email: str) -> str:
    identifier = str(uuid4())
    post_to_create = PostInDB(identifier=identifier, owner=user_email, **post.model_dump()).model_dump()
    
    posts.insert_one(post_to_create)
    append_post_to_owner(user_email, identifier)

    return identifier

def insert_pokemon_to_post(user_email: str, pokemon: Pokemon):
    insert_pokemon = PokemonInDB(owner=user_email, **pokemon.model_dump()).model_dump()
    
    pokemons.insert_one(insert_pokemon)
    post_data = get_post_by_identifier(pokemon['identifier']).model_dump()
    qnt = post_data['elements']
    if qnt >= 3:
        return "You can't add more than 3 elements on a post"

    increase_qnt(post_identifier, qnt)
    # append_post_to_owner(user_email)

def insert_item_to_post(user_email: str, item: Item):
    insert_item = ItemInDB(owner=user_email, **item.model_dump()).model_dump()
    
    items.insert_one(insert_item)
    post_data = get_post_by_identifier(item['identifier']).model_dump()
    qnt = post_data['elements']
    if qnt >= 3:
        return "You can't add more than 3 elements on a post"

    increase_qnt(post_identifier, qnt)
    # append_post_to_owner(user_email)

# Função para converter MongoDB ObjectId para string
def serialize_document(document):
    """Converte um documento MongoDB para um formato serializável em JSON."""
    if isinstance(document, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else serialize_document(v)) for k, v in document.items()}
    elif isinstance(document, list):
        return [serialize_document(item) for item in document]
    return document

def get_post_by_identifier(identifier: str):
    # Obter o post
    post_data = posts.find_one({'identifier': identifier})
    if not post_data:
        return {"error": "Post not found"}

    # Obter os itens associados
    post_items = list(items.find({'identifier': identifier}))
    post_items_serialized = [serialize_document(item) for item in post_items]

    # Obter os pokemons associados
    post_pokemons = list(pokemons.find({'identifier': identifier}))
    post_pokemons_serialized = [serialize_document(pokemon) for pokemon in post_pokemons]

    # Criar o PostDetails
    post_data_serialized = serialize_document(post_data)
    post_details = PostDetails(
        **post_data_serialized,
        items=post_items_serialized,
        pokemons=post_pokemons_serialized
    )

    return post_details

def get_post_by_owner(user_email: str):
    posts_data = list(posts.find({'owner': user_email}))
    posts_serialized = serialize_document(posts_data)

    for post in posts_serialized:
        identifier = post['identifier']
        # Obter os itens associados
        post_items = list(items.find({'identifier': identifier}))
        post_items_serialized = [serialize_document(item) for item in post_items]

        # Obter os pokemons associados
        post_pokemons = list(pokemons.find({'identifier': identifier}))
        post_pokemons_serialized = [serialize_document(pokemon) for pokemon in post_pokemons]

        post['items'] = post_items
        post['pokemons'] = post_pokemons

    # Criando instâncias de PostInDB para retorno
    post_models = [PostDetails(**post) for post in posts_serialized]

    return post_models

def increase_qnt(post_identifier: str, qnt: int):
    posts.update_one({
    'identifier': post_identifier,   
    },
    { "$set": { "elements": qnt + 1 } }
    )

def get_all_posts():
    posts_cursor = posts.find()
    posts_list = list(posts_cursor)
    posts_serialized = [serialize_document(post) for post in posts_list]

    for post in posts_serialized:
        identifier = post['identifier']
        # Obter os itens associados
        post_items = list(items.find({'identifier': identifier}))
        post_items_serialized = [serialize_document(item) for item in post_items]

        # Obter os pokemons associados
        post_pokemons = list(pokemons.find({'identifier': identifier}))
        post_pokemons_serialized = [serialize_document(pokemon) for pokemon in post_pokemons]

        post['items'] = post_items
        post['pokemons'] = post_pokemons

    # Criando instâncias de PostInDB para retorno
    post_models = [PostDetails(**post) for post in posts_serialized]

    return post_models

def delete_post(identifier: str, user_email: str):
    # Verificar se o post existe
    post = posts.find_one({'identifier': identifier})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Verificar se o usuário é o dono do post
    if post['owner'] != user_email:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    # Remover o post da lista de posts do usuário
    user_posts = get_user(user_email).posts
    user_posts.remove(identifier)
    posts.update_one({'identifier': identifier}, {'$set': {'posts': user_posts}})

    post_items = items.find({'identifier': identifier})
    post_pokemons = pokemons.find({'identifier': identifier})

    for item in post_items:
        items.delete_one(item)

    for pokemon in post_pokemons:
        pokemons.delete_one(pokemon)
    
    # Remover o post da lista de posts de todos os usuários
    for user in users.find():
        if identifier in user['posts']:
            user_posts = user['posts']
            user_posts.remove(identifier)
            users.update_one({'email': user['email']}, {'$set': {'posts': user_posts}})

    # Remover o post do banco de dados
    posts.delete_one({'identifier': identifier})