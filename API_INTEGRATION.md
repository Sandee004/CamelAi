# CamelAI Backend API Integration Guide

This document provides comprehensive information about the CamelAI Backend API endpoints, authentication, request/response formats, and integration guidelines for frontend developers.

## Base URL
```
http://localhost:5000
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. Most endpoints support optional authentication, while some require it.

### Authentication Flow
1. Request OTP using `/api/auth`
2. Verify OTP using `/api/verify-otp` to get access token
3. Include token in Authorization header: `Bearer <token>`

---

## API Endpoints

### 1. Health Check

#### GET `/ping`
Simple health check endpoint.

**Response:**
```
Pong
```
**Status Code:** `200`

---

### 2. Authentication Endpoints

#### POST `/api/auth`
Request OTP for phone-based authentication (login or signup).

**Request Body:**
```json
{
  "phone": "+1234567890"
}
```

**Response (Success):**
```json
{
  "message": "OTP sent to +1234567890"
}
```
**Status Code:** `200`

**Response (Error):**
```json
{
  "error": "Phone number is required"
}
```
**Status Code:** `400`

---

#### POST `/api/verify-otp`
Verify OTP and receive access token.

**Request Body:**
```json
{
  "phone": "+1234567890",
  "otp": "123456"
}
```

**Note:** In development mode, you can use OTP `"0000"` for any phone number.

**Response (Success):**
```json
{
  "message": "OTP verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1
}
```
**Status Code:** `200`

**Response (Error):**
```json
{
  "error": "Invalid phone or OTP"
}
```
**Status Code:** `404` or `400`

---

### 3. User Management

#### PUT `/api/user/settings`
Update user profile information. **Requires Authentication.**

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890"
}
```

**Response (Success):**
```json
{
  "message": "Settings updated successfully",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }
}
```
**Status Code:** `200`

**Response (Error):**
```json
{
  "error": "Email already exists"
}
```
**Status Code:** `400`

---

### 4. AI Beauty Analysis

#### POST `/api/rate-image`
Analyze a single camel image for beauty rating across multiple categories.

**Headers:**
```
Authorization: Bearer <access_token> (optional)
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_url": "https://example.com/camel.jpg",
  "gender": "male" // optional: "male", "female", or "unknown"
}
```

**Response (Success):**
```json
{
  "beauty_ratings": {
    "head_beauty": {
      "attributes": [
        {
          "name": "ear_shape",
          "score": 8.5,
          "priority": "high",
          "analysis": "Well-proportioned ears..."
        }
      ],
      "category_score": 8.2
    },
    "neck_beauty": {
      "attributes": [...],
      "category_score": 7.8
    },
    "body_beauty": {
      "attributes": [...],
      "category_score": 8.0
    },
    "leg_beauty": {
      "attributes": [...],
      "category_score": 7.5
    }
  },
  "overall_score": 8.1,
  "attribute_weights": {
    "high": 5,
    "medium": 3,
    "low": 1
  },
  "categories_analyzed": ["head_beauty", "neck_beauty", "body_beauty", "leg_beauty"],
  "processing_time": 12.456,
  "validation": {
    "contains_camel": true,
    "visible_parts": {
      "head": true,
      "neck": true,
      "body": true,
      "legs": true
    },
    "overall_suitability": true,
    "feedback": "Image contains a clearly visible camel suitable for analysis"
  }
}
```
**Status Code:** `200`

**Response (Validation Error):**
```json
{
  "error": "No camel detected in image",
  "validation": {
    "contains_camel": false,
    "overall_suitability": false,
    "feedback": "The image does not contain a camel."
  },
  "suggestions": [
    "Please upload an image that clearly shows a camel",
    "Ensure the camel is the main subject of the image",
    "Make sure the image quality is good and not blurry"
  ]
}
```
**Status Code:** `400`

**Response (Cached Result):**
Same as success response but includes additional fields:
```json
{
  // ... same as success response
  "cached": true,
  "cached_at": "2024-01-15T10:30:00.000Z"
}
```

---

#### POST `/api/compare-beauty`
Compare beauty between two camel images.

**Headers:**
```
Authorization: Bearer <access_token> (optional)
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_url_1": "https://example.com/camel1.jpg",
  "image_url_2": "https://example.com/camel2.jpg",
  "gender": "female" // optional: "male", "female", or "unknown"
}
```

**Response (Success):**
```json
{
  "comparison_result": {
    "camel_1": {
      "image_url": "https://example.com/camel1.jpg",
      "beauty_ratings": {
        "head_beauty": {
          "attributes": [...],
          "category_score": 8.2
        },
        // ... other categories
      },
      "overall_score": 8.1,
      "category_scores": {
        "head_beauty": 8.2,
        "neck_beauty": 7.8,
        "body_beauty": 8.0,
        "leg_beauty": 7.5
      },
      "validation": {
        "contains_camel": true,
        "overall_suitability": true
      }
    },
    "camel_2": {
      "image_url": "https://example.com/camel2.jpg",
      "beauty_ratings": {
        // ... similar structure
      },
      "overall_score": 7.3,
      "category_scores": {
        "head_beauty": 7.1,
        "neck_beauty": 7.2,
        "body_beauty": 7.5,
        "leg_beauty": 7.4
      },
      "validation": {
        "contains_camel": true,
        "overall_suitability": true
      }
    },
    "winner": "Camel 1",
    "score_difference": 0.8,
    "gender": "female"
  },
  "attribute_weights": {
    "high": 5,
    "medium": 3,
    "low": 1
  },
  "categories_analyzed": ["head_beauty", "neck_beauty", "body_beauty", "leg_beauty"],
  "processing_time": 24.789
}
```
**Status Code:** `200`

**Response (Error):**
```json
{
  "error": "Camel 1 analysis failed",
  "details": {
    "error": "No camel detected in Camel 1",
    "validation": {
      "contains_camel": false,
      "overall_suitability": false
    }
  }
}
```
**Status Code:** `400`

---

### 5. Legacy/Additional Endpoints

#### GET `/account`
Get account details (from auth blueprint).

**Response:**
```json
{
  "msg": "Gotten account details"
}
```
**Status Code:** `200`

---

## Data Models

### User Model
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890"
}
```

### Beauty Analysis Attribute
```json
{
  "name": "ear_shape",
  "score": 8.5,
  "priority": "high", // "high", "medium", or "low"
  "analysis": "Detailed analysis text explaining the score"
}
```

### Validation Result
```json
{
  "contains_camel": true,
  "visible_parts": {
    "head": true,
    "neck": true,
    "body": true,
    "legs": true
  },
  "overall_suitability": true,
  "feedback": "Detailed explanation",
  "missing_parts": [], // Array of missing parts if any
  "quality_issues": [] // Array of quality issues if any
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Descriptive error message"
}
```

**401 Unauthorized:**
```json
{
  "msg": "Missing Authorization Header"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to process request"
}
```

---

## Authentication Implementation

### Frontend Authentication Flow

1. **Request OTP:**
```javascript
const requestOTP = async (phone) => {
  const response = await fetch('/api/auth', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ phone })
  });
  return response.json();
};
```

2. **Verify OTP:**
```javascript
const verifyOTP = async (phone, otp) => {
  const response = await fetch('/api/verify-otp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ phone, otp })
  });
  const data = await response.json();
  
  if (data.access_token) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user_id', data.user_id);
  }
  
  return data;
};
```

3. **Make Authenticated Requests:**
```javascript
const makeAuthenticatedRequest = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return fetch(url, {
    ...options,
    headers
  });
};
```

---

## Beauty Analysis Integration

### Single Image Analysis
```javascript
const analyzeImage = async (imageUrl, gender = 'unknown') => {
  const response = await makeAuthenticatedRequest('/api/rate-image', {
    method: 'POST',
    body: JSON.stringify({
      image_url: imageUrl,
      gender: gender
    })
  });
  
  return response.json();
};
```

### Image Comparison
```javascript
const compareImages = async (imageUrl1, imageUrl2, gender = 'unknown') => {
  const response = await makeAuthenticatedRequest('/api/compare-beauty', {
    method: 'POST',
    body: JSON.stringify({
      image_url_1: imageUrl1,
      image_url_2: imageUrl2,
      gender: gender
    })
  });
  
  return response.json();
};
```

---

## Caching

The API implements intelligent caching for beauty analysis results:

- **Image Hashing:** Images are hashed using perceptual hashing algorithms
- **Cache Duration:** Results are cached indefinitely until manually cleared
- **Cache Indicators:** Responses include `cached: true` and `cached_at` timestamp for cached results
- **Validation Caching:** Even validation failures are cached to avoid repeated processing

---

## Rate Limiting & Performance

- **Processing Time:** Beauty analysis typically takes 10-30 seconds per image
- **Concurrent Processing:** Comparison endpoint processes both images concurrently
- **Model Used:** GPT-5 for beauty analysis, GPT-4o for validation
- **Response Format:** All AI responses use structured JSON format

---

## Development Notes

### Development Mode Features
- **SMS Disabled:** OTP sending is disabled, check console for OTP values
- **Hardcoded OTP:** Use `"0000"` as OTP for any phone number in development
- **Debug Mode:** Flask runs in debug mode with detailed error messages

### Environment Variables Required
```env
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=sqlite:///camelai.db
```

---

## Swagger Documentation

The API includes Swagger documentation available at:
```
http://localhost:5000/apidocs/
```

This provides an interactive interface to test all endpoints directly from the browser.