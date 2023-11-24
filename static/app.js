// Sample product data
const products = [
    { name: 'airpods', imageUrl: 'static/images/airpods.jpg', viewUrl: 'airpods.html' },
    { name: 'doorbell', imageUrl: 'static/images/doorbell.jpg', viewUrl: 'doorbell.html' },
    { name: 'electric_cooker', imageUrl: 'static/images/e_cooker.jpg', viewUrl: 'electric_cooker.html' },
    { name: 'meta_quest_3', imageUrl: 'static/images/meta_quest_3.jpg', viewUrl: 'meta_quest_3.html' },
    { name: 'vacuum', imageUrl: 'static/images/vaccum.jpg', viewUrl: 'vaccum.html' },
];

// Function to create product elements
function createProductElement(product) {
    const productDiv = document.createElement('div');
    productDiv.classList.add('product');

    // Wrap the image inside an anchor tag
    const anchor = document.createElement('a');
    anchor.href = product.viewUrl;

    const image = document.createElement('img');
    image.src = product.imageUrl;
    image.alt = product.name;

    anchor.appendChild(image);
    productDiv.appendChild(anchor);

    return productDiv;
}

// Function to initialize the page
function initPage() {
    const productContainer = document.getElementById('productContainer');

    // Create and append product elements to the container
    products.forEach(product => {
        const productElement = createProductElement(product);
        productContainer.appendChild(productElement);
    });
}

// Initialize the page when the DOM is ready
document.addEventListener('DOMContentLoaded', initPage);
