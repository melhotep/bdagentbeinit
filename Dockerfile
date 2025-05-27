FROM apify/actor-python:3.11

# Copy package files
COPY package.json ./

# Copy source code
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir apify-client==1.4.0 \
    playwright==1.32.0 \
    requests==2.32.3 \
    beautifulsoup4==4.13.4 \
    asyncio==3.4.3

# Install Playwright browsers
RUN python -m playwright install chromium

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/usr/src/app

# Run the actor
CMD ["python", "-m", "src"]
