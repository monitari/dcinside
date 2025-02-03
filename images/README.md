# Images Directory

This directory is used to store images downloaded from the DCINSIDE gallery. (due to Person gallery)

## Usage

1. The `gallery_info.py` script downloads gallery cover images and saves them in this directory.
2. Images are saved with unique filenames based on the hash of the URL.
3. Already downloaded images will not be downloaded again.

## Notes

- This directory is automatically created when the script is run.
- Images stored in this directory are referenced during script execution.
- Unnecessary images can be manually deleted.

## Examples

- `images/jingburger_1234567890.jpg`
- `images/anothergallery_0987654321.jpg`