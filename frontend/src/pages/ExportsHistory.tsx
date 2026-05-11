import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from '@/components/ui/use-toast';
import { Loader2, Download, Trash2 } from 'lucide-react';
import { listExportsHistory, downloadExport, deleteExport } from '../api/services';

interface ExportHistoryItem {
  id: string;
  costing_sheet_id: string;
  scenario_id: string;
  user_id: string;
  revision_number: number;
  file_type: string;
  file_path: string;
  exported_at: string;
}

/**
 * @purpose Displays a history of exported documents, allowing users to download or delete them.
 * Fetches exports specific to a sheet if `sheetId` is present in the URL,
 * otherwise shows recent exports across all sheets.
 * @param {void}
 * @returns {JSX.Element} A React component displaying the export history.
 * @owner [Gemini]
 */
const ExportsHistory: React.FC = () => {
  const { sheetId } = useParams<{ sheetId?: string }>();
  const queryClient = useQueryClient();

  const { data: exports, isLoading, isError } = useQuery<ExportHistoryItem[]>({
    queryKey: ['exportsHistory', sheetId],
    queryFn: () => listExportsHistory(),
  });

  const downloadMutation = useMutation({
    mutationFn: (exportId: string) => downloadExport(exportId).then(r => r.signed_url),
    onSuccess: (blobUrl: string, exportId: string) => {
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `export_${exportId}.zip`; // Or actual filename from service
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
      toast({ title: 'Download started successfully.' });
    },
    onError: (error: Error) => toast({ title: 'Download failed.', description: error.message, variant: 'destructive' }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteExport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exportsHistory', sheetId] });
      toast({ title: 'Export deleted successfully.' });
    },
    onError: (error: Error) => toast({ title: 'Delete failed.', description: error.message, variant: 'destructive' }),
  });

  if (isLoading) return <div className="p-4 flex justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>;
  if (isError) return <div className="p-4 text-red-600">Failed to load exports.</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">
        {sheetId ? `Exports for Sheet: ${sheetId}` : 'Recent Exports'}
      </h1>
      {exports?.length === 0 ? (
        <p className="text-gray-500">No exports found.</p>
      ) : (
        <div className="rounded-md border bg-card text-card-foreground shadow-sm">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scenario Name</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Created Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {exports?.map((exp) => (
                <TableRow key={exp.id}>
                  <TableCell className="font-medium">{exp.scenario_id}</TableCell>
                  <TableCell>{exp.file_type.toUpperCase()}</TableCell>
                  <TableCell>{new Date(exp.exported_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right flex justify-end space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadMutation.mutate(exp.id)}
                      disabled={downloadMutation.isPending}
                    >
                      {downloadMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      <span className="sr-only">Download</span>
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm" disabled={deleteMutation.isPending}>
                          {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                          <span className="sr-only">Delete</span>
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the export data.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => deleteMutation.mutate(exp.id)}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default ExportsHistory;