const searchBox = document.querySelector('#twotabsearchtextbox');
const searchButton = document.querySelector('#nav-search-submit-button');

if (searchBox && searchButton) {
  searchBox.focus();
  searchBox.value = '';
  searchBox.value = 'r2d2';
  searchButton.click();
}