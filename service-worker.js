// Service Worker 不使用缓存，每次都从网络获取最新内容

// 安装事件：直接激活，不进行缓存
self.addEventListener('install', (event) => {
  console.log('Service Worker 安装中...');
  event.waitUntil(self.skipWaiting());
});

// 激活事件：立即激活，清理所有旧缓存
self.addEventListener('activate', (event) => {
  console.log('Service Worker 激活中...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('删除缓存:', cacheName);
          return caches.delete(cacheName);
        })
      );
    })
    .then(() => self.clients.claim())
  );
});

// Fetch事件：直接从网络获取资源，不使用缓存
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // 检查响应是否有效
        if (!response || response.status !== 200) {
          console.log('请求失败:', event.request.url);
          return response;
        }
        console.log('从网络获取资源:', event.request.url);
        return response;
      })
      .catch((error) => {
        console.log('网络请求失败:', error);
        throw error;
      })
  );
});