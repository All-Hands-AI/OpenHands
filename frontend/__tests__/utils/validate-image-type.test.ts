import { validateImageType, getValidImageFiles } from '#/utils/validate-image-type';
import { describe, expect, it } from 'vitest';

describe('validateImageType', () => {
  it('should accept supported image types', () => {
    const supportedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    supportedTypes.forEach((type) => {
      const file = new File([''], 'test.jpg', { type });
      expect(validateImageType(file)).toBe(true);
    });
  });

  it('should reject unsupported image types', () => {
    const unsupportedTypes = ['image/bmp', 'image/tiff', 'application/pdf', 'text/plain'];
    unsupportedTypes.forEach((type) => {
      const file = new File([''], 'test.jpg', { type });
      expect(validateImageType(file)).toBe(false);
    });
  });
});

describe('getValidImageFiles', () => {
  it('should separate valid and invalid files', () => {
    const files = [
      new File([''], 'test1.jpg', { type: 'image/jpeg' }),
      new File([''], 'test2.bmp', { type: 'image/bmp' }),
      new File([''], 'test3.png', { type: 'image/png' }),
      new File([''], 'test4.pdf', { type: 'application/pdf' }),
    ];

    const { validFiles, invalidFiles } = getValidImageFiles(files);

    expect(validFiles).toHaveLength(2);
    expect(invalidFiles).toHaveLength(2);
    expect(validFiles[0].type).toBe('image/jpeg');
    expect(validFiles[1].type).toBe('image/png');
    expect(invalidFiles[0].type).toBe('image/bmp');
    expect(invalidFiles[1].type).toBe('application/pdf');
  });

  it('should handle empty array', () => {
    const { validFiles, invalidFiles } = getValidImageFiles([]);
    expect(validFiles).toHaveLength(0);
    expect(invalidFiles).toHaveLength(0);
  });
});
