# Train Information API

A Node.js Express API for retrieving train information.

## Prerequisites

- Node.js (version 14 or higher)
- npm (Node Package Manager)

## Installation

1. **Download and Extract**
   - Download the project files
   - Extract the archive to your desired location

2. **Navigate to Project Directory**
   ```bash
   cd project-directory-name
   ```

3. **Install Dependencies**
   ```bash
   npm install
   ```

4. **Start the Application**
   ```bash
   npm start
   ```

## Usage

The server will start on port 3001. You can access the API endpoints at:

```
http://localhost:3001
```

### Available Endpoints

- **Test Endpoint**: `GET /test`
  - Returns a simple test message to verify the API is working

- **Train Information**: `GET /api/train/trainInfo/:trainNumber`
  - Retrieves information for a specific train
  - Replace `:trainNumber` with the actual train number
  - Example: `GET /api/train/trainInfo/22177`

## Development

To run the application in development mode with auto-restart:

```bash
npm run dev
```

## Project Structure

```
├── routes/
│   └── index.js          # API routes
├── controller/
│   └── train.controller.js   # Business logic
├── package.json
└── server.js             # Main application file
```

## Technologies Used

- Express.js
- Morgan (HTTP request logger)
- CORS (Cross-Origin Resource Sharing)

## Support

For issues or questions, please refer to the project documentation or contact the development team.