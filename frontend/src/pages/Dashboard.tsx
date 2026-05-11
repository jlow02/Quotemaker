import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { format } from 'date-fns';

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
    CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
    DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { listCostingSheets, createCostingSheet } from '../api/services';

// Mock type for a CostingSheet to satisfy immediate needs
interface CostingSheet {
  id: string;
  title: string;
  clientOrganization: string;
  status: 'Draft' | 'Approved' | 'Rejected' | 'Pending';
  createdAt: string;
}

const newCostingSheetSchema = z.object({
  title: z.string().min(3, { message: 'Title must be at least 3 characters.' }),
  clientOrganization: z.string().min(3, { message: 'Client organization must be at least 3 characters.' }),
});

type NewCostingSheetFormValues = z.infer<typeof newCostingSheetSchema>;

/**
 * @purpose Renders the dashboard displaying a list of costing sheets.
 *          Allows users to create new costing sheets through a modal form.
 * @returns {JSX.Element} The Dashboard page component.
 * @owner [Gemini]
 */
const Dashboard = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [isNewSheetModalOpen, setIsNewSheetModalOpen] = useState(false);

  const {
    data: costingSheets,
    isLoading,
    isError,
    error,
  } = useQuery<CostingSheet[], Error>({
    queryKey: ['costingSheets'],
    queryFn: () => listCostingSheets() as unknown as Promise<CostingSheet[]>,
  });

  const createSheetMutation = useMutation<CostingSheet, Error, NewCostingSheetFormValues>({
    mutationFn: (values: NewCostingSheetFormValues) => createCostingSheet({
      quote_title: values.title,
      client_name: values.clientOrganization,
    }) as unknown as Promise<CostingSheet>,
    onSuccess: (newSheet) => {
      queryClient.invalidateQueries({ queryKey: ['costingSheets'] });
      setIsNewSheetModalOpen(false);
      navigate(`/sheets/${newSheet.id}`);
    },
    onError: (err) => {
      console.error('Failed to create costing sheet:', err);
      // Optionally set an error message state to display in the modal
    },
  });

  const newSheetForm = useForm<NewCostingSheetFormValues>({
    resolver: zodResolver(newCostingSheetSchema),
    defaultValues: {
      title: '',
      clientOrganization: '',
    },
  });

  const onNewSheetSubmit = async (values: NewCostingSheetFormValues) => {
    createSheetMutation.mutate(values);
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading costing sheets...</div>;
  }

  if (isError) {
    return <div className="p-8 text-center text-red-500">Error: {error?.message || 'Failed to fetch sheets'}</div>;
  }

  return (
    <div className="container mx-auto p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Costing Sheets</h1>
        <Dialog open={isNewSheetModalOpen} onOpenChange={setIsNewSheetModalOpen}>
          <DialogTrigger asChild>
            <Button>New Costing Sheet</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create New Costing Sheet</DialogTitle>
              <DialogDescription>
                Enter the details for your new costing sheet.
              </DialogDescription>
            </DialogHeader>
            <Form {...newSheetForm}>
              <form onSubmit={newSheetForm.handleSubmit(onNewSheetSubmit)} className="space-y-4">
                <FormField
                  control={newSheetForm.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Title</FormLabel>
                      <FormControl>
                        <Input placeholder="Project X Costing" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={newSheetForm.control}
                  name="clientOrganization"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Client Organization</FormLabel>
                      <FormControl>
                        <Input placeholder="Acme Corp." {...field} />
                      </FormControl>
                      <p className='text-sm text-muted-foreground'>
                        Start typing to search for existing organizations (not implemented in this example).
                      </p>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full" disabled={createSheetMutation.isPending}>
                  {createSheetMutation.isPending ? 'Creating...' : 'Create Sheet'}
                </Button>
                {createSheetMutation.isError && (
                  <p className="text-sm font-medium text-red-500">
                    Failed to create: {createSheetMutation.error?.message}
                  </p>
                )}
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {costingSheets && costingSheets.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {costingSheets.map((sheet) => (
            <Card
              key={sheet.id}
              className="cursor-pointer transition-colors hover:border-primary"
              onClick={() => navigate(`/sheets/${sheet.id}`)}
            >
              <CardHeader>
                <CardTitle className="text-xl">{sheet.title}</CardTitle>
                <CardDescription>{sheet.clientOrganization}</CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <Badge variant="default">{sheet.status}</Badge>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {format(new Date(sheet.createdAt), 'MMM dd, yyyy')}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="mt-12 text-center text-gray-600 dark:text-gray-400">
          <p className="text-lg">No costing sheets found.</p>
          <p className="mt-2">Click "New Costing Sheet" to create your first one!</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;