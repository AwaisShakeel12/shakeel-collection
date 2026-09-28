from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Point this to your running Django DRF backend
DRF_API_URL = os.getenv("DRF_API_URL", "https://shakeelcollection.pythonanywhere.com/api")

# ==========================================
# HOME & PAGE ROUTES
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/home/")
            home_data = res.json()
        except Exception:
            home_data = {}
            
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"home_data": home_data}
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    # No login checks. Just render the admin page directly.
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/category/{slug}/")
            data = res.json() if res.status_code == 200 else {"category": {"name": "Not Found"}, "products": []}
        except Exception:
            data = {"category": {"name": "Error"}, "products": []}
            
    return templates.TemplateResponse(
        request=request, 
        name="category.html", 
        context={"data": data, "slug": slug}
    )

@app.get("/product/{slug}", response_class=HTMLResponse)
async def product_page(request: Request, slug: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/product/{slug}/")
            product = res.json() if res.status_code == 200 else None
        except Exception:
            product = None
            
    if not product: 
        return templates.TemplateResponse(
            request=request, 
            name="index.html", 
            context={"home_data": {}}
        )
        
    return templates.TemplateResponse(
        request=request, 
        name="detail.html", 
        context={"product": product}
    )

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    return templates.TemplateResponse(request=request, name="cart.html")

# ==========================================
# ADMIN PROXY ROUTES (No Auth/Keys Required)
# ==========================================

@app.post("/admin/upload")
async def admin_upload(
    name: str = Form(...), description: str = Form(""),
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
            
        # Direct proxy, no admin key headers
        res = await client.post(f"{DRF_API_URL}/admin/product/create/", data=data, files=files)
        return res.json()

@app.get("/api/admin/products")
async def get_products(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{DRF_API_URL}/admin/products/")
            return res.json()
        except Exception as e:
            return {"error": str(e)}

@app.put("/api/admin/product/{pk}")
async def update_product_proxy(request: Request, pk: int):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            res = await client.put(f"{DRF_API_URL}/admin/product/{pk}/update/", json=body)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

@app.delete("/api/admin/product/{pk}")
async def delete_product_proxy(request: Request, pk: int):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.delete(f"{DRF_API_URL}/admin/product/{pk}/delete/")
            return res.json()
        except Exception as e:
            return {"error": str(e)}

# ==========================================
# CHECKOUT PROXY
# ==========================================

@app.post("/api/checkout-proxy")
async def checkout_proxy(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{DRF_API_URL}/checkout/whatsapp/", json=body)
        return res.json()
