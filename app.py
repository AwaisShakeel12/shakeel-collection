from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🌟 UPDATED: Pointing to your LIVE PythonAnywhere Backend
DRF_API_URL = os.getenv("DRF_API_URL", "https://shakeelcollection.pythonanywhere.com/api")

# --- HOME ROUTE ---
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/home/")
            home_data = res.json()
        except Exception: 
            home_data = {}
            
    # 🌟 UPDATED: Now points to index.html instead of home.html
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"home_data": home_data}
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.post("/admin/upload")
async def admin_upload(
    admin_key: str = Form(...), name: str = Form(...), description: str = Form(""),
    category: int = Form(...), price: float = Form(...), discount_price: float = Form(None),
    image_url: str = Form(""), is_featured: str = Form(""), is_sold: str = Form(""),
    image_file: UploadFile = File(None)
):
    async with httpx.AsyncClient() as client:
        files = {}
        if image_file and image_file.filename:
            content = await image_file.read()
            files['image_file'] = (image_file.filename, content, image_file.content_type)
        
        featured_bool = True if is_featured == "on" else False
        sold_bool = True if is_sold == "on" else False
        
        data = {
            "name": name, "description": description, "category": category, "price": price,
            "is_featured": featured_bool, "is_sold": sold_bool
        }
        if discount_price: data["discount_price"] = discount_price
        if image_url: data["image_url"] = image_url
            
        headers = {"X-Admin-Key": admin_key}
        res = await client.post(f"{DRF_API_URL}/admin/product/create/", data=data, files=files, headers=headers)
        return res.json()

# --- OTHER ROUTES ---
@app.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/category/{slug}/")
            data = res.json() if res.status_code == 200 else {"category": {"name": "Not Found"}, "products": []}
        except Exception: data = {"category": {"name": "Error"}, "products": []}
    return templates.TemplateResponse(request=request, name="category.html", context={"data": data, "slug": slug})

@app.get("/product/{slug}", response_class=HTMLResponse)
async def product_page(request: Request, slug: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/product/{slug}/")
            product = res.json() if res.status_code == 200 else None
        except Exception: product = None
    if not product: return templates.TemplateResponse(request=request, name="index.html", context={"home_data": {}})
    return templates.TemplateResponse(request=request, name="detail.html", context={"product": product})

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    return templates.TemplateResponse(request=request, name="cart.html")

@app.post("/api/checkout-proxy")
async def checkout_proxy(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{DRF_API_URL}/checkout/whatsapp/", json=body)
        return res.json()