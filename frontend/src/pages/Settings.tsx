import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Loader2, Plus, Trash2, Edit, Save } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import {
  listGlobalTnc,
  createGlobalTnc,
  deleteGlobalTnc,
  getSettings,
  updateSetting,
} from '../api/services';

interface TncItem {
  id: string;
  bullet_point: string;
}

interface SettingItem {
  key: string;
  value: string;
}

/**
 * @purpose Provides a centralized settings management interface with various tabs
 * for different application configurations, including Organisations, Products,
 * Templates, Terms & Conditions, and System settings.
 * @param {void}
 * @returns {JSX.Element} A React component for the settings page.
 * @owner [Gemini]
 */
const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const [newTncContent, setNewTncContent] = useState('');
  const [editingSettingKey, setEditingSettingKey] = useState<string | null>(null);
  const [editingSettingValue, setEditingSettingValue] = useState('');

  // T&C Tab Logic
  const { data: tncList, isLoading: isLoadingTnc } = useQuery<TncItem[]>({
    queryKey: ['globalTnc'],
    queryFn: listGlobalTnc,
  });

  const addTncMutation = useMutation({
    mutationFn: createGlobalTnc,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['globalTnc'] });
      setNewTncContent('');
      toast({ title: 'T&C added successfully.' });
    },
    onError: (error: Error) => toast({ title: 'Failed to add T&C.', description: error.message, variant: 'destructive' }),
  });

  const deleteTncMutation = useMutation({
    mutationFn: deleteGlobalTnc,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['globalTnc'] });
      toast({ title: 'T&C deleted successfully.' });
    },
    onError: (error: Error) => toast({ title: 'Failed to delete T&C.', description: error.message, variant: 'destructive' }),
  });

  // System Tab Logic
  const { data: systemSettings, isLoading: isLoadingSettings } = useQuery<SettingItem[]>({
    queryKey: ['systemSettings'],
    queryFn: getSettings,
  });

  const updateSettingMutation = useMutation({
    mutationFn: (args: { key: string; value: string }) => updateSetting(args.key, args.value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemSettings'] });
      setEditingSettingKey(null);
      toast({ title: 'Setting updated successfully.' });
    },
    onError: (error: Error) => toast({ title: 'Failed to update setting.', description: error.message, variant: 'destructive' }),
  });

  const handleEditSetting = (key: string, value: string) => {
    setEditingSettingKey(key);
    setEditingSettingValue(value);
  };

  const handleSaveSetting = (key: string) => {
    updateSettingMutation.mutate({ key, value: editingSettingValue });
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      <Tabs defaultValue="organisations" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="organisations">Organisations</TabsTrigger>
          <TabsTrigger value="products">Products</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="tnc">T&C</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="organisations" className="mt-4">
          <h2 className="text-2xl font-semibold mb-4">Organisation Management</h2>
          {/* Placeholder for OrgManager Component */}
          <p className="text-gray-500">Organisation settings would be managed here.</p>
        </TabsContent>

        <TabsContent value="products" className="mt-4">
          <h2 className="text-2xl font-semibold mb-4">Product Library</h2>
          {/* Placeholder for ProductLibrary Component */}
          <p className="text-gray-500">Product library management would be here.</p>
        </TabsContent>

        <TabsContent value="templates" className="mt-4">
          <h2 className="text-2xl font-semibold mb-4">Templates List</h2>
          {/* Placeholder for TemplatesList Component */}
          <p className="text-gray-500">Template configurations would be found here.</p>
        </TabsContent>

        <TabsContent value="tnc" className="mt-4">
          <h2 className="text-2xl font-semibold mb-4">Global Terms & Conditions</h2>
          <div className="flex space-x-2 mb-4">
            <Input
              placeholder="New T&C content"
              value={newTncContent}
              onChange={(e) => setNewTncContent(e.target.value)}
              className="flex-grow"
            />
            <Button onClick={() => addTncMutation.mutate({ bullet_point: newTncContent })} disabled={addTncMutation.isPending || !newTncContent}>
              {addTncMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Add
            </Button>
          </div>
          {isLoadingTnc ? (
            <div className="flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : (tncList as TncItem[] | undefined)?.length === 0 ? (
            <p className="text-gray-500">No global T&C found.</p>
          ) : (
            <div className="rounded-md border bg-card text-card-foreground shadow-sm">
              <Table>
                <TableBody>
                  {(tncList as TncItem[] | undefined)?.map((tnc) => (
                    <TableRow key={tnc.id}>
                      <TableCell>{tnc.bullet_point}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => deleteTncMutation.mutate(tnc.id)}
                          disabled={deleteTncMutation.isPending}
                        >
                          {deleteTncMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                          <span className="sr-only">Delete T&C</span>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="system" className="mt-4">
          <h2 className="text-2xl font-semibold mb-4">System Settings</h2>
          {isLoadingSettings ? (
            <div className="flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : systemSettings?.length === 0 ? (
            <p className="text-gray-500">No system settings found.</p>
          ) : (
            <div className="rounded-md border bg-card text-card-foreground shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Key</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {systemSettings?.map((setting) => (
                    <TableRow key={setting.key}>
                      <TableCell className="font-medium">{setting.key}</TableCell>
                      <TableCell>
                        {editingSettingKey === setting.key ? (
                          <Input
                            value={editingSettingValue}
                            onChange={(e) => setEditingSettingValue(e.target.value)}
                            className="h-8"
                          />
                        ) : (
                          setting.value
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {editingSettingKey === setting.key ? (
                          <Button
                            size="sm"
                            onClick={() => handleSaveSetting(setting.key)}
                            disabled={updateSettingMutation.isPending}
                          >
                            {updateSettingMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditSetting(setting.key, setting.value)}
                          >
                            <Edit className="h-4 w-4" /> Edit
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;