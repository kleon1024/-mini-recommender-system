import api from './api';

// 获取设备信息
const getDeviceInfo = () => {
  const userAgent = navigator.userAgent;
  let deviceType = 'desktop';
  let os = 'unknown';
  
  // 简单的设备类型检测
  if (/mobile/i.test(userAgent)) {
    deviceType = 'mobile';
  } else if (/tablet|ipad/i.test(userAgent)) {
    deviceType = 'tablet';
  }
  
  // 简单的操作系统检测
  if (/windows/i.test(userAgent)) {
    os = 'Windows';
  } else if (/macintosh|mac os x/i.test(userAgent)) {
    os = 'macOS';
  } else if (/android/i.test(userAgent)) {
    os = 'Android';
  } else if (/iphone|ipad|ipod/i.test(userAgent)) {
    os = /ipad/i.test(userAgent) ? 'iPadOS' : 'iOS';
  } else if (/linux/i.test(userAgent)) {
    os = 'Linux';
  }
  
  return { type: deviceType, os };
};

// 埋点SDK类
class Tracker {
  constructor(userId) {
    this.userId = userId || 'anonymous';
    this.deviceInfo = getDeviceInfo();
    this.queue = [];
    this.isProcessing = false;
    this.viewObserver = null;
    this.stayTimeMap = new Map(); // 记录停留时间
    
    // 定期发送队列中的事件
    setInterval(() => this.processQueue(), 2000);
  }
  
  // 设置用户ID
  setUserId(userId) {
    this.userId = userId;
  }
  
  // 生成事件ID
  generateEventId() {
    return `e_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // 添加事件到队列
  addToQueue(event) {
    this.queue.push(event);
  }
  
  // 处理队列中的事件
  async processQueue() {
    if (this.isProcessing || this.queue.length === 0) return;
    
    this.isProcessing = true;
    const events = [...this.queue];
    this.queue = [];
    
    try {
      await api.post(`/api/events/batch`, { events });
    } catch (error) {
      console.error('Failed to send events:', error);
      // 失败时将事件放回队列
      this.queue = [...events, ...this.queue];
    } finally {
      this.isProcessing = false;
    }
  }
  
  // 上报事件
  trackEvent(postId, eventType, source, extra = {}) {
    const event = {
      event_id: this.generateEventId(),
      user_id: this.userId,
      post_id: postId,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      source,
      device_info: this.deviceInfo,
      extra
    };
    
    this.addToQueue(event);
    return event;
  }
  
  // 曝光埋点
  trackView(postId, source) {
    return this.trackEvent(postId, 'view', source);
  }
  
  // 点击埋点
  trackClick(postId, source) {
    return this.trackEvent(postId, 'click', source);
  }
  
  // 点赞埋点
  trackLike(postId, source) {
    return this.trackEvent(postId, 'like', source);
  }
  
  // 收藏埋点
  trackFavorite(postId, source) {
    return this.trackEvent(postId, 'favorite', source);
  }
  
  // 播放埋点
  trackPlay(postId, source) {
    return this.trackEvent(postId, 'play', source);
  }
  
  // 开始记录停留时间
  startStayTime(postId) {
    this.stayTimeMap.set(postId, Date.now());
  }
  
  // 结束记录停留时间并上报
  endStayTime(postId, source) {
    if (!this.stayTimeMap.has(postId)) return;
    
    const startTime = this.stayTimeMap.get(postId);
    const endTime = Date.now();
    const duration = Math.floor((endTime - startTime) / 1000); // 转换为秒
    
    this.stayTimeMap.delete(postId);
    
    if (duration >= 1) { // 只记录停留1秒以上的
      return this.trackEvent(postId, 'stay', source, { duration });
    }
  }
  
  // 初始化曝光观察器
  initViewObserver(selector = '.post-card', source = 'home') {
    if (!window.IntersectionObserver) return;
    
    // 销毁之前的观察器
    if (this.viewObserver) {
      this.viewObserver.disconnect();
    }
    
    // 创建新的观察器
    this.viewObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const postId = entry.target.dataset.postId;
        if (!postId) return;
        
        if (entry.isIntersecting) {
          // 元素进入视口，记录曝光并开始计时
          this.trackView(postId, source);
          this.startStayTime(postId);
        } else {
          // 元素离开视口，结束计时并上报停留时间
          this.endStayTime(postId, source);
        }
      });
    }, { threshold: 0.5 }); // 当50%的元素可见时触发
    
    // 观察所有匹配的元素
    document.querySelectorAll(selector).forEach(el => {
      this.viewObserver.observe(el);
    });
  }
  
  // 销毁观察器
  destroyViewObserver() {
    if (this.viewObserver) {
      this.viewObserver.disconnect();
      this.viewObserver = null;
    }
  }
}

// 创建单例
let instance = null;

export const getTracker = (userId) => {
  if (!instance) {
    instance = new Tracker(userId);
  } else if (userId) {
    instance.setUserId(userId);
  }
  return instance;
};

export default Tracker;