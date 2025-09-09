import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

// ✅ Custom metrics
const errorCount = new Counter('errors');
const loginTrend = new Trend('login_duration');
const checkoutTrend = new Trend('checkout_duration');
const successRate = new Rate('successful_requests');

export const options = {
  stages: [
    { duration: '1m', target: 1000 },   // ramp-up
    { duration: '2m', target: 5000 },   // steady load
    { duration: '1m', target: 10000 },  // spike
    { duration: '2m', target: 5000 },   // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'], // global threshold
    'successful_requests': ['rate>0.95'], // ensure 95% success
  },
};

export default function () {
  // Pick random endpoint
  const endpoints = [
    { url: 'https://test.k6.io/', name: 'home' },
    { url: 'https://test.k6.io/news.php', name: 'news' },
    { url: 'https://test.k6.io/contact.php', name: 'contact' },
    { url: 'https://test.k6.io/login.php', name: 'login' },
  ];
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];

  const res = http.get(endpoint.url, { tags: { name: endpoint.name } });

  // Checks for response validation
  const passed = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });

  if (!passed) {
    errorCount.add(1);
  }
  successRate.add(passed);

  // Track trends for specific endpoints
  if (endpoint.name === 'login') {
    loginTrend.add(res.timings.duration);
  } else if (endpoint.name === 'contact') {
    checkoutTrend.add(res.timings.duration);
  }

  sleep(Math.random() * 2); // simulate think time
}
