# HTTP File Server Lab

This lab implements a comprehensive HTTP file server in Python using socket programming, with support for multiple file types, directory browsing, and nested directories.

## Files

- `server.py` - The main web server implementation
- `client.py` - HTTP client for testing the server
- `content/` - Directory containing sample files to serve
  - `index.html` - Main website with PDF collection
  - `*.pdf` - Sample PDF documents
  - `*.png` - Sample image files
  - `books/` - Subdirectory with PDF books
  - `images/` - Subdirectory with PNG images

## Features

### Server Features
- **Command-line directory argument**: Server takes directory to serve as argument
- **Multiple file type support**: HTML, PNG, PDF with proper MIME types
- **Directory listing**: Automatic HTML generation for directory browsing
- **Nested directory support**: Full support for subdirectories
- **Error handling**: 404 for missing files, 500 for server errors
- **Binary file support**: Proper handling of binary files (PNG, PDF)

### Client Features
- **File type detection**: Automatically handles different file types
- **HTML display**: Shows HTML content in terminal
- **File download**: Saves PNG and PDF files to downloads directory
- **HTTP response parsing**: Proper parsing of HTTP headers and body
- **Error handling**: Displays appropriate error messages

## How to Run

### 1. Start the Web Server

```bash
cd src
python server.py ./content
```

The server will start listening on port 6789 and serve files from the `content` directory.

### 2. Test with a Browser

Open a web browser and navigate to:
```
http://localhost:6789/
```

You should see the main website with directory listing.

Browse to subdirectories:
```
http://localhost:6789/books/
http://localhost:6789/images/
```

### 3. Test with the HTTP Client

#### Download HTML files (displayed in terminal):
```bash
python client.py localhost 6789 index.html
```

#### Download PDF files (saved to downloads/):
```bash
python client.py localhost 6789 sample1.pdf
python client.py localhost 6789 books/book1.pdf
```

#### Download PNG files (saved to downloads/):
```bash
python client.py localhost 6789 logo.png
python client.py localhost 6789 images/screenshot1.png
```

## Directory Structure

```
content/
├── index.html          # Main website
├── sample1.pdf         # Sample PDF document
├── manual.pdf           # Technical manual
├── research.pdf        # Research paper
├── logo.png           # Company logo
├── diagram.png        # System diagram
├── books/             # Subdirectory with books
│   ├── book1.pdf
│   └── book2.pdf
└── images/            # Subdirectory with images
    ├── screenshot1.png
    └── screenshot2.png
```

## Advanced Features

### Directory Listing
- Automatic HTML generation for directory browsing
- Styled with CSS for better presentation
- Parent directory navigation
- File type indicators

### MIME Type Support
- `text/html` for HTML files
- `image/png` for PNG images
- `application/pdf` for PDF documents
- Proper Content-Type headers

### Error Handling
- 404 Not Found for missing files/directories
- 500 Internal Server Error for server issues
- Proper HTTP status codes and error pages

## Testing Scenarios

1. **Basic file serving**: Access individual files directly
2. **Directory browsing**: Navigate through directories
3. **Nested directories**: Test subdirectory functionality
4. **File downloads**: Use client to download different file types
5. **Error handling**: Test with non-existent files
6. **Network testing**: Test with friends on local network

## Implementation Details

- **Socket programming**: Uses Python's socket module
- **HTTP parsing**: Manual HTTP request/response parsing
- **File handling**: Binary and text file support
- **URL decoding**: Proper handling of URL-encoded paths
- **MIME types**: Automatic content type detection
- **Error pages**: HTML error pages for better user experience
