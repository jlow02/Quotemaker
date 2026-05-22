/**
 * @purpose Ambient TypeScript declarations for the html2pdf.js CDN library.
 *          Loaded via <script> tag in index.html. No npm install required.
 * @owner [DeepSeek]
 */

interface Html2PdfOptions {
  margin?: number | number[];
  filename?: string;
  image?: { type: string; quality: number };
  html2canvas?: { scale: number; useCORS: boolean };
  jsPDF?: { unit: string; format: string; orientation: string };
}

interface Html2PdfChain {
  set(opts: Html2PdfOptions): Html2PdfChain;
  save(filename?: string): Promise<void>;
}

interface Html2PdfInstance {
  from(el: HTMLElement): Html2PdfChain;
}

declare function html2pdf(): Html2PdfInstance;
