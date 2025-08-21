# Use official Node.js LTS version for stability
FROM node:20-alpine

# Set working directory inside container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json first (for efficient caching)
COPY package*.json ./

# Install dependencies (production only)
RUN npm install --omit=dev

# Copy the rest of the application code
COPY . .

# Expose application port (change if needed)
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]
