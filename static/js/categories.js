const categoryState = {
  categories: [],
  editingId: null,
  deletingId: null,
};

const categoryElement = (id) => document.getElementById(id);

function showCategoryToast(title, message, isError = false) {
  const toast = categoryElement("toast");
  categoryElement("toastTitle").textContent = title;
  categoryElement("toastMessage").textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3000);
}

function closeCategoryModal() {
  categoryElement("categoryModal").classList.remove("active");
  categoryElement("categoryForm").reset();
  categoryElement("categoryId").value = "";
  categoryState.editingId = null;
  categoryElement("modalTitle").textContent = "Add Category";
  categoryElement("saveCategoryBtn").textContent = "Add Category";
}

function renderCategories() {
  const search = categoryElement("searchInput").value.trim().toLowerCase();
  const status = categoryElement("statusFilter").value;
  const filtered = categoryState.categories.filter((category) => {
    const matchesSearch =
      category.name.toLowerCase().includes(search) ||
      (category.description || "").toLowerCase().includes(search);
    return matchesSearch && (!status || category.status === status);
  });
  const body = categoryElement("categoryTableBody");
  body.innerHTML = filtered
    .map(
      (category) => `
        <tr>
          <td>${category.id}</td>
          <td>${category.name}</td>
          <td>${category.description || "-"}</td>
          <td>${category.status}</td>
          <td>
            <button type="button" class="edit-category" data-id="${category.id}">Edit</button>
            <button type="button" class="delete-category" data-id="${category.id}">Delete</button>
          </td>
        </tr>`
    )
    .join("");
  categoryElement("emptyState").style.display = filtered.length ? "none" : "block";
  categoryElement("totalCategories").textContent = categoryState.categories.length;
  categoryElement("activeCategories").textContent = categoryState.categories.filter(
    (category) => category.status === "active"
  ).length;
  categoryElement("inactiveCategories").textContent = categoryState.categories.filter(
    (category) => category.status === "inactive"
  ).length;
}

async function loadCategories() {
  const response = await fetch("/api/categories");
  const result = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || "Unable to load categories.");
  }
  categoryState.categories = result.categories;
  renderCategories();
}

async function saveCategory(event) {
  event.preventDefault();
  const id = categoryState.editingId;
  const payload = {
    name: categoryElement("categoryName").value.trim(),
    description: categoryElement("categoryDescription").value.trim(),
    status: categoryElement("categoryStatus").value,
  };
  const response = await fetch(id ? `/api/categories/${id}` : "/api/categories", {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || "Unable to save category.");
  }
  closeCategoryModal();
  await loadCategories();
  showCategoryToast("Success", result.message);
}

async function deleteCategory() {
  const response = await fetch(`/api/categories/${categoryState.deletingId}`, {
    method: "DELETE",
  });
  const result = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || "Unable to delete category.");
  }
  categoryElement("deleteModal").classList.remove("active");
  categoryState.deletingId = null;
  await loadCategories();
  showCategoryToast("Success", result.message);
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadCategories();
  } catch (error) {
    showCategoryToast("Error", error.message, true);
  }

  categoryElement("openAddModal").addEventListener("click", () => {
    categoryElement("categoryModal").classList.add("active");
  });
  categoryElement("emptyAddBtn").addEventListener("click", () => {
    categoryElement("categoryModal").classList.add("active");
  });
  categoryElement("closeModal").addEventListener("click", closeCategoryModal);
  categoryElement("cancelBtn").addEventListener("click", closeCategoryModal);
  categoryElement("categoryForm").addEventListener("submit", async (event) => {
    try {
      await saveCategory(event);
    } catch (error) {
      showCategoryToast("Error", error.message, true);
    }
  });
  categoryElement("searchInput").addEventListener("input", renderCategories);
  categoryElement("statusFilter").addEventListener("change", renderCategories);
  categoryElement("cancelDelete").addEventListener("click", () =>
    categoryElement("deleteModal").classList.remove("active")
  );
  categoryElement("confirmDelete").addEventListener("click", async () => {
    try {
      await deleteCategory();
    } catch (error) {
      showCategoryToast("Error", error.message, true);
    }
  });
  categoryElement("categoryTableBody").addEventListener("click", (event) => {
    const id = Number(event.target.dataset.id);
    if (event.target.classList.contains("edit-category")) {
      const category = categoryState.categories.find((item) => item.id === id);
      categoryState.editingId = id;
      categoryElement("categoryId").value = id;
      categoryElement("categoryName").value = category.name;
      categoryElement("categoryDescription").value = category.description || "";
      categoryElement("categoryStatus").value = category.status;
      categoryElement("modalTitle").textContent = "Edit Category";
      categoryElement("saveCategoryBtn").textContent = "Save Changes";
      categoryElement("categoryModal").classList.add("active");
    }
    if (event.target.classList.contains("delete-category")) {
      categoryState.deletingId = id;
      categoryElement("deleteCategoryName").textContent =
        categoryState.categories.find((item) => item.id === id).name;
      categoryElement("deleteModal").classList.add("active");
    }
  });
});
