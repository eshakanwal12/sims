const productState = { products: [], categories: [] };

const productElement = (id) => document.getElementById(id);

function showProductError(message) {
  console.error(message);
  window.alert(message);
}

function renderProducts() {
  const search = productElement("searchProduct").value.trim().toLowerCase();
  const category = productElement("categoryFilter").value;
  const products = productState.products.filter((product) => {
    const matchesSearch =
      product.product_name.toLowerCase().includes(search) ||
      product.sku.toLowerCase().includes(search);
    return matchesSearch && (!category || String(product.category_id) === category);
  });
  productElement("productsTableBody").innerHTML = products
    .map(
      (product) => `
        <tr>
          <td>${product.product_name}</td>
          <td>${product.sku}</td>
          <td>${product.category_name}</td>
          <td>${product.stock_quantity}</td>
          <td>${Number(product.selling_price).toFixed(2)}</td>
        </tr>`
    )
    .join("");
  productElement("totalProducts").textContent = productState.products.length;
  productElement("totalStock").textContent = productState.products.reduce(
    (total, product) => total + Number(product.stock_quantity || 0),
    0
  );
  productElement("inventoryValue").textContent = productState.products
    .reduce(
      (total, product) =>
        total + Number(product.purchase_price || 0) * Number(product.stock_quantity || 0),
      0
    )
    .toFixed(2);
  productElement("lowStock").textContent = productState.products.filter(
    (product) => Number(product.stock_quantity) <= Number(product.minimum_stock)
  ).length;
}

async function loadProducts() {
  const [productsResponse, categoriesResponse] = await Promise.all([
    fetch("/api/products"),
    fetch("/api/categories"),
  ]);
  const products = await productsResponse.json();
  const categories = await categoriesResponse.json();
  if (!productsResponse.ok || !Array.isArray(products)) {
    throw new Error(products.message || "Unable to load products.");
  }
  if (!categoriesResponse.ok || !categories.success) {
    throw new Error(categories.message || "Unable to load categories.");
  }
  productState.products = products;
  productState.categories = categories.categories;
  productElement("productCategory").innerHTML = productState.categories
    .map((item) => `<option value="${item.id}">${item.name}</option>`)
    .join("");
  productElement("categoryFilter").innerHTML =
    '<option value="">All Categories</option>' +
    productState.categories
      .map((item) => `<option value="${item.id}">${item.name}</option>`)
      .join("");
  renderProducts();
}

async function saveProduct(event) {
  event.preventDefault();
  const payload = {
    product_name: productElement("productName").value.trim(),
    sku: productElement("productSku").value.trim(),
    category_id: Number(productElement("productCategory").value),
    purchase_price: Number(productElement("purchasePrice").value),
    selling_price: Number(productElement("sellingPrice").value),
    stock_quantity: Number(productElement("stockQuantity").value),
    minimum_stock: Number(productElement("minimumStock").value),
    description: productElement("productDescription").value.trim(),
  };
  const response = await fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || "Unable to save product.");
  }
  productElement("productForm").reset();
  productElement("productModal").classList.remove("active");
  await loadProducts();
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadProducts();
  } catch (error) {
    showProductError(error.message);
  }
  productElement("searchProduct").addEventListener("input", renderProducts);
  productElement("categoryFilter").addEventListener("change", renderProducts);
  productElement("addProductBtn").addEventListener("click", () =>
    productElement("productModal").classList.add("active")
  );
  productElement("closeModalBtn").addEventListener("click", () =>
    productElement("productModal").classList.remove("active")
  );
  productElement("cancelBtn").addEventListener("click", () =>
    productElement("productModal").classList.remove("active")
  );
  productElement("productForm").addEventListener("submit", async (event) => {
    try {
      await saveProduct(event);
    } catch (error) {
      showProductError(error.message);
    }
  });
});
