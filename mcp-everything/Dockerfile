FROM node:22-alpine

WORKDIR /app

# Install curl and netcat for healthchecks
RUN apk add --no-cache curl netcat-openbsd

# Install the OFFICIAL MCP everything server from npm
RUN npm install -g @modelcontextprotocol/server-everything@latest

# Expose the divine port
EXPOSE 3000

# Set environment variable for port
ENV PORT=3000

# Run the everything server in streamableHttp mode
CMD ["npx", "@modelcontextprotocol/server-everything", "streamableHttp"]