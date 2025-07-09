# Study Material Manager

A modern, feature-rich desktop application for organizing and managing study materials with an elegant dark-themed UI.

## Features

- 📚 **Material Management**
  - Add, edit, view, and delete study materials
  - Rich text content support
  - Tag-based organization
  - File attachment support for various formats
  - Automatic tracking of creation and modification dates

- 🔍 **Smart Search**
  - Real-time search through titles and tags
  - Instant results as you type
  - Case-insensitive searching

- 📎 **File Handling**
  - Drag and drop file attachments
  - Support for multiple file formats:
    - Documents (PDF, DOCX, TXT)
    - Images (PNG, JPG, JPEG)
    - Videos (MP4, AVI, MOV)
    - Other file types
  - Direct file opening with system default applications

- 🎨 **Modern UI**
  - Elegant dark theme
  - Material Design-inspired color scheme
  - Responsive layout
  - Smooth animations
  - User-friendly interface

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/StudyMaterialManager.git
   cd StudyMaterialManager
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Drive Integration (Optional):**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project.
   - Enable the **Google Drive API** for your project.
   - Create credentials for a **Desktop app**.
   - Download the credentials as `credentials.json` and place it in the root directory of the application.

4. Run the application:
   ```bash
   python StudyMaterialManager.py
   ```

## Requirements

- Python 3.7+
- customtkinter
- tkinterdnd2
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- SQLite3 (included with Python)


## Usage

1. **Adding Materials**
   - Click the "Add" button or use the keyboard shortcut
   - Fill in the title (required)
   - Add optional content and tags
   - Attach files by dragging and dropping or using the browse button

2. **Managing Materials**
   - Double-click any item to view details
   - Use the action buttons for edit, delete, and other operations
   - Search materials using the search bar
   - Open attached files directly from the application

3. **Organizing with Tags**
   - Add comma-separated tags to materials
   - Search by tags to filter materials
   - Tags are displayed alongside titles in the main list

## Database

The application uses SQLite3 for data storage with the following schema:

```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    tags TEXT,
    file_path TEXT,
    date_added TEXT,
    last_modified TEXT
)
```

The database file (`study_materials.db`) is automatically created in the application directory.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Drag and drop functionality powered by [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2)

## Support

If you encounter any issues or have suggestions, please [open an issue](https://github.com/yourusername/StudyMaterialManager/issues). 
