# OCR Implementation Notes

## Performance Comparison

Initial testing between EasyOCR and macOS Vision framework:

### EasyOCR
- Requires ~2.3s initialization (one-time cost)
- First read: ~0.4s
- Subsequent reads: ~0.3s
- Cross-platform compatibility
- Requires loading ML model into memory

### Vision Framework
- No separate initialization
- First read: ~0.5s (includes framework initialization)
- Subsequent reads: ~0.15s (2x faster than EasyOCR)
- Native macOS only (11.0+)
- Lower memory footprint (uses system resources)

## Implementation Strategy
- Vision framework is primary OCR method
  - Must be tried first for all inputs
  - Never skip Vision unless it fails
  - Fall back to EasyOCR only if Vision fails
- Image format handling:
  - Always pass both CGImage and PNG filepath together
  - Never convert CGImage in memory
  - Vision uses CGImage directly
  - EasyOCR and Claude use PNG file
  - Conversion between formats happens at capture time only
- Image format requirements:
  - Always pass both CGImage and PNG filepath together
  - Never try to convert CGImage in memory
  - Vision uses CGImage directly
  - EasyOCR and Claude use PNG file
  - Conversion between formats happens at capture time only
- OCRProcessor class handles all text extraction
  - Encapsulates both Vision and EasyOCR methods
  - Maintains singleton pattern for EasyOCR reader
  - Manages queuing for thread safety
  - Provides single interface: get_text_from_image()
- Use Vision framework as primary OCR on macOS 11+
- Fall back to EasyOCR for:
  - Older macOS versions
  - Error cases
  - Cross-platform compatibility

## Testing Notes

### Simple Text Performance
- Both frameworks equally accurate on basic test cases
- Vision framework faster after initial run (~0.15s vs ~0.3s)

### Real-world Screenshot Results (Forum webpage)
- Vision framework:
  - Faster: 0.41s
  - Better formatting preservation
  - More accurate special characters (→, •)
  - Better handling of UI elements
  - Preserved timestamps accurately

- EasyOCR:
  - Slower: 3.42s
  - Some character confusion (e.g., '/' as 'f')
  - Inconsistent with special characters
  - More prone to spacing/formatting issues

### Areas for Further Testing
  - Real-world screenshots
  - Different fonts and sizes
  - Multiple languages
  - Special characters
  - Various background colors

## Logging Guidelines
- Log OCR method in use: "[DEBUG] Using Vision OCR" or "[DEBUG] Using EasyOCR"
- Log fallback cases with reason: "[DEBUG] Vision OCR failed, falling back to EasyOCR: {error}"
- Skip timestamps in logs
- Focus on OCR method selection over performance details

## Testing Patterns

### Test Image Creation
- Use 400x100px white background
- Place text in center (around 50,40)
- Use simple test strings like "TEST"
- Avoid font size parameters (not supported)
- Save to test_data/ subdirectory
- Clean up test files in tearDown

### Vision Framework Testing
- Mock both VNRecognizeTextRequest and VNImageRequestHandler
- Mock observation.text() return value
- Mock handler.performRequests_error_ return value
- Test error cases by raising exceptions
- Mock at module level where function is imported (e.g. 'meadow.core.monitor.CGWindowListCopyWindowInfo')
- Use actual Quartz constants in mock data (kCGWindowOwnerName, etc)

### EasyOCR Testing  
- Test as fallback when Vision fails
- Verify text detection rather than exact matches
- Check queue state before/after processing
- Clean up reader instance between tests
- Keep tests focused due to slow initialization
- Avoid multiple EasyOCR calls in same test

### Test Image Creation
- Use 400x100px white background
- Place text in center (around 50,40)
- Use simple test strings like "TEST"
- Avoid font size parameters (not supported)
- Save to test_data/ subdirectory
- Clean up test files in tearDown

### Vision Framework Testing
- Mock both VNRecognizeTextRequest and VNImageRequestHandler
- Mock observation.text() return value
- Mock handler.performRequests_error_ return value
- Test error cases by raising exceptions

### EasyOCR Testing  
- Test as fallback when Vision fails
- Verify text detection rather than exact matches
- Check queue state before/after processing
- Clean up reader instance between tests

## Development Notes
- Vision/Quartz imports may show as missing in pylint
- These are valid imports on macOS despite pylint errors
- No need to suppress these warnings as they're macOS-specific modules
- Import order: standard libs → third party → macOS frameworks

### macOS Framework Import Patterns
- UTType constants should be imported from Quartz.CoreServices:
  ```python
  from Quartz.CoreServices import kUTTypePNG
  ```
  - Available through Quartz.CoreServices module
  - Provides access to deprecated CoreServices constants
  - Required for image type identification

### Development Environment
- Use type hints and modern IDE for framework import warnings
- Configure pylint/mypy for better static analysis:
  ```ini
  # setup.cfg
  [mypy]
  platform=darwin
  python_version=3.9
  
  [pylint]
  extension-pkg-whitelist=Quartz,CoreServices
  ```
- Consider using pyright for better macOS framework type checking
## Image Format Requirements

### Vision OCR
- Requires CGImage input
- Native macOS format, no conversion needed from Quartz capture
- Must be valid CGImage instance, not CGImage data

### EasyOCR
- Accepts only:
  - File path (string) - PREFERRED
  - URL (string) 
  - Raw bytes
  - Numpy array
- Prefer using file paths when possible:
  - Most reliable method
  - Avoids memory manipulation issues
  - Simplifies error handling
  - Lets EasyOCR handle image loading
- Cannot process CGImage directly
- Convert CGImage using:
  ```python
  np_array = np.frombuffer(CGDataProviderCopyData(cg_image), dtype=np.uint8)
  ```

### Image Saving
- Any format that supports np.array can be used
- PIL not required, can save directly from numpy array
- CGImage can be saved directly using ImageIO framework

### Best Practices
- Keep native CGImage format throughout Vision OCR path
- For EasyOCR, save CGImage to temporary file and pass the path
- Avoid direct memory manipulation when possible
- Avoid unnecessary PIL conversions
- Use native frameworks for saving when possible
- Handle format conversion in OCRProcessor class, not in calling code
