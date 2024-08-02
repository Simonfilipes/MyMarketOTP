from fastapi import APIRouter, Depends, HTTPException
from app.models.models import *
import app.models.pyrodb as pyrodb
from app.validation.auth import *
from app.validation.validator import Validate


router = APIRouter()
validate = Validate()


# --> Post Creation <--
@router.post("/create")
async def create_post(post_info: Post, user: User = Depends(get_current_active_user)) -> dict:

    user_email = user.model_dump()['email']

    if v := validate.post(post_info):
        raise HTTPException(400, detail=v)

    post_id = pyrodb.create_post(post_info, user_email)
    return {"status": 200, "detail": "Post created succesfully", "post_id": post_id}


@router.post("/pokemon")
async def add_pokemon(pokemon: Pokemon, user: User = Depends(get_current_active_user)) -> dict:
    
    user = user.model_dump()
    user_email = user['email']
    anuncio_id = pokemon.model_dump()['identifier']

    if v := validate.validate_post(anuncio_id, user):
        raise HTTPException(400, detail=v)
    
    if v := validate.validate_pokemon(pokemon):
        raise HTTPException(400, detail=v)
    
    if v := pyrodb.insert_pokemon_to_post(user_email, pokemon):
        raise HTTPException(400, detail=v)
        
    return {"status": 200, "detail": "Pokemon added to the post succesfully", 'user_data': user}


@router.post("/item")
async def add_item(item: Item, user: User = Depends(get_current_active_user)) -> dict:

    user_email = user.model_dump()['email']
    anuncio_id = item.model_dump()['identifier']

    if v := validate.validate_post(anuncio_id, user):
        raise HTTPException(400, detail=v)

    if v := validate.validate_items(item):
        raise HTTPException(400, detail=v)
    
    if v := pyrodb.insert_item_to_post(user_email, item):
        raise HTTPException(400, detail=v)
        
    return {"status": 200, "detail": "Item added to the post succesfully"}

# Get posts
@router.get('/{post_identifier}')
def get_post_by_identifier(post_identifier: str):
    post = pyrodb.get_post_by_identifier(post_identifier)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post

@router.get('/owner/{user_email}')
def get_posts_by_owner(user_email: str):
    posts = pyrodb.get_post_by_owner(user_email)
    if not posts:
        raise HTTPException(status_code=404, detail="User posts not found")
    return posts

@router.get('')
def get_all_posts():
    posts = pyrodb.get_all_posts()
    if not posts:
        raise HTTPException(status_code=404, detail="Posts not found")
        
    return posts

@router.delete('/{identifier}')
async def delete_post(identifier: str, user: User = Depends(get_current_active_user)):
    user_email = user.model_dump()['email']
    if v := validate.validate_post(identifier, user):
        raise HTTPException(400, detail=v)

    pyrodb.delete_post(identifier, user_email)
    return {"status": 200, "detail": "Post deleted succesfully"}