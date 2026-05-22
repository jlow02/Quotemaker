/**
 * @purpose In-app quote preview panel. Fetches rendered HTML from the backend preview
 *          endpoint and displays it in an iframe. Provides a single-click PDF download
 *          via html2pdf.js (CDN loaded in index.html) — no print dialog is shown.
 * @owner [DeepSeek]
 */
import React, { useEffect, useState } from 'react';
import { Loader2, FileDown } from 'lucide-react';
import { Button } from '../ui/button';
import { getScenarioPreviewHtml } from '../../api/services';

interface QuotePreviewProps {
  /** Active scenario UUID. Pass empty string to hide the panel. */
  scenarioId: string;
}

/**
 * @purpose Renders a live HTML preview of the quote in an iframe and allows
 *          single-click silent PDF download via html2pdf.js.
 * @param props.scenarioId UUID of the active scenario; empty string hides the panel.
 * @owner [DeepSeek]
 */
const QuotePreview: React.FC<QuotePreviewProps> = ({ scenarioId }) => {
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  useEffect(() => {
    if (!scenarioId) {
      setHtmlContent(null);
      setError(null);
      return;
    }

    const fetchPreview = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const html = await getScenarioPreviewHtml(scenarioId);
        setHtmlContent(html);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load preview');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPreview();
  }, [scenarioId]);

  /**
   * @purpose Downloads the current quote preview as a PDF using html2pdf.js.
   *          Creates a hidden off-screen div, renders the HTML into it, generates
   *          the PDF, then removes the div. No print dialog is shown.
   * @owner [DeepSeek]
   */
  const handleDownloadPdf = async (): Promise<void> => {
    if (!htmlContent) return;
    setIsDownloading(true);

    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.left = '-9999px';
    container.style.top = '0';
    container.style.width = '794px';
    container.innerHTML = htmlContent;
    document.body.appendChild(container);

    try {
      await html2pdf()
        .from(container)
        .set({
          margin: 0,
          filename: 'NEXTAN_Quote.pdf',
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        })
        .save();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate PDF');
    } finally {
      document.body.removeChild(container);
      setIsDownloading(false);
    }
  };

  if (!scenarioId) return null;

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Quote Preview</h2>
        <Button
          variant="outline"
          onClick={handleDownloadPdf}
          disabled={!htmlContent || isDownloading}
        >
          {isDownloading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <FileDown className="mr-2 h-4 w-4" />
          )}
          {isDownloading ? 'Generating PDF...' : 'Download PDF'}
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      )}

      {error && (
        <div className="text-red-500 text-sm py-4">{error}</div>
      )}

      {htmlContent && !isLoading && (
        <iframe
          srcDoc={htmlContent}
          title="Quote Preview"
          sandbox="allow-scripts allow-same-origin"
          style={{
            width: '100%',
            height: '900px',
            border: '1px solid #e2e8f0',
            borderRadius: '4px',
            background: '#e0e0e0',
          }}
        />
      )}
    </div>
  );
};

export default QuotePreview;
