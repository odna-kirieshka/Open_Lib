document.addEventListener('DOMContentLoaded', function() {
  // Находим все кнопки для поделиться
  const shareButtons = document.querySelectorAll('.share-button');
  
  // Добавляем обработчик для каждой кнопки
  shareButtons.forEach(button => {
      button.addEventListener('click', function() {
          // Получаем данные
          const network = this.getAttribute('data-network');
          const bookId = this.getAttribute('data-book-id');
          
          // Отправляем статистику на сервер
          registerShare(bookId, network);
          
          // Если это кнопка копирования, обрабатываем ее особо
          if (network === 'copy') {
              copyToClipboard(this);
              return false; // Предотвращаем переход по ссылке
          }
      });
  });
  
  // Функция отправки статистики на сервер
  function registerShare(bookId, network) {
    console.log('ОНО ЖИВОЕ (но в JS)');
    
      fetch('/api/share', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({
              book_id: bookId,
              network: network
          })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              // Обновляем счетчик на странице
              const shareCountElement = document.getElementById('share-count');
              if (shareCountElement) {
                  shareCountElement.textContent = data.share_count;
              }
          }
      })
      .catch(error => {
          console.error('Ошибка при отправке статистики:', error);
      });
  }
  
  // Функция копирования в буфер обмена
  function copyToClipboard(button) {
      // Получаем URL для копирования
      const url = button.getAttribute('data-url');
      
      // Создаём временный input для копирования
      const tempInput = document.createElement('input');
      tempInput.value = url;
      document.body.appendChild(tempInput);
      
      // Выделяем и копируем текст
      tempInput.select();
      document.execCommand('copy');
      
      // Удаляем временный элемент
      document.body.removeChild(tempInput);
      
      // Меняем текст кнопки на время, чтобы показать успешное копирование
      const originalContent = button.innerHTML;
      button.innerHTML = '<i class="bi bi-check"></i>';
      
      // Возвращаем исходный контент через 2 секунды
      setTimeout(() => {
          button.innerHTML = originalContent;
      }, 2000);
  }
});