import { FileItem } from '@/types/api';

export const sanitizeFileName = (fileName: string): string => {
  return fileName.replace(/\s+/g, '_');
};

export const getFileExtension = (fileName: string): string => {
  return fileName.split('.').pop()?.toLowerCase() || '';
};

export const isPdfFile = (fileName: string): boolean => {
  return getFileExtension(fileName) === 'pdf';
};

export const isMarkdownFile = (fileName: string): boolean => {
  return getFileExtension(fileName) === 'md';
};

export const getTranslationName = (pdfName: string): string => {
  const nameWithoutExt = pdfName.replace(/\.[^/.]+$/, '');
  return `${nameWithoutExt}.md`;
};

export const getUntranslatedFiles = (files: FileItem[]): FileItem[] => {
  return files.filter(file => 
    isPdfFile(file.name) && !file.has_translation
  );
};

export const sortFiles = (files: FileItem[], sortBy: 'name' | 'translated' | 'date'): FileItem[] => {
  const sorted = [...files];
  
  switch (sortBy) {
    case 'name':
      return sorted.sort((a, b) => a.name.localeCompare(b.name));
    case 'translated':
      return sorted.sort((a, b) => {
        if (a.has_translation === b.has_translation) {
          return a.name.localeCompare(b.name);
        }
        return a.has_translation ? -1 : 1;
      });
    case 'date':
      return sorted.sort((a, b) => 
        new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime()
      );
    default:
      return sorted;
  }
};

export const searchFiles = (files: FileItem[], query: string): FileItem[] => {
  if (!query.trim()) return files;
  
  const lowerQuery = query.toLowerCase();
  return files.filter(file => 
    file.name.toLowerCase().includes(lowerQuery)
  );
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN');
};