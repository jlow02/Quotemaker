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
import { Loader2, Plus, Trash2, Edit, Save, X } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  listGlobalTnc,
  createGlobalTnc,
  deleteGlobalTnc,
  getSettings,
  updateSetting,
  listTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
} from '../api/services';

interface TncItem {
  id: string;
  bullet_point: string;
}

interface SettingItem {
  key: string;
  value: string;
}

interface Template {
  id: string;
  name: string;
  notes_exclusions: string[] | null;
  created_at: string;
  updated_at: string;
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

  // Template state
  const [newTemplateDialogOpen, setNewTemplateDialogOpen] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateNotes, setNewTemplateNotes] = useState('');
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const [newTncContent, setNewTncContent] = useState('');
  const [editingSettingKey, setEditingSettingKey] = useState<string | null>(null);
  const [editingSettingValue, setEditingSettingValue] = useState('');

  const templatesQuery = useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: listTemplates,
  });

  /**
   * Mutation to create a new template.
   */
  const createMutation = useMutation({
    mutationFn: (data: { name: string; notes_exclusions: string[] }) => createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast({ title: 'Template created successfully' });
      setNewTemplateDialogOpen(false);
      setNewTemplateName('');
      setNewTemplateNotes('');
    },
    onError: () => {
      toast({ title: 'Failed to create template', variant: 'destructive' });
    },
  });

  /**
   * Mutation to update an existing template.
   */
  const updateMutation = useMutation({
    mutationFn: (data: { id: string; name: string; notes_exclusions: string[] }) =>
      updateTemplate(data.id, { name: data.name, notes_exclusions: data.notes_exclusions }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast({ title: 'Template updated successfully' });
      setEditingTemplateId(null);
    },
    onError: () => {
      toast({ title: 'Failed to update template', variant: 'destructive' });
    },
  });

  /**
   * Mutation to delete a template.
   */
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast({ title: 'Template deleted successfully' });
      setDeleteConfirmId(null);
    },
    onError: () => {
      toast({ title: 'Failed to delete template', variant: 'destructive' });
    },
  });

  /**
   * Handles creating a new template from the dialog form.
   */
  const handleCreateTemplate = () => {
    if (!newTemplateName.trim()) {
      toast({ title: 'Template name is required', variant: 'destructive' });
      return;
    }
    const notesArray = newTemplateNotes.split('\n').filter(Boolean);
    createMutation.mutate({ name: newTemplateName.trim(), notes_exclusions: notesArray });
  };

  /**
   * Starts inline editing for a template.
   * 
   * @param {Template} template - The template to edit
   */
  const startEditing = (template: Template) => {
    setEditingTemplateId(template.id);
    setEditName(template.name);
    setEditNotes((template.notes_exclusions || []).join('\n'));
  };

  /**
   * Cancels the current inline editing.
   */
  const cancelEditing = () => {
    setEditingTemplateId(null);
    setEditName('');
    setEditNotes('');
  };

  /**
   * Saves the inline-edited template.
   * 
   * @param {string} id - The template ID
   */
  const saveEditing = (id: string) => {
    if (!editName.trim()) {
      toast({ title: 'Template name is required', variant: 'destructive' });
      return;
    }
    const notesArray = editNotes.split('\n').filter(Boolean);
    updateMutation.mutate({ id, name: editName.trim(), notes_exclusions: notesArray });
  };

  /**
   * Confirms deletion of a template.
   * 
   * @param {string} id - The template ID to delete
   */
  const confirmDelete = (id: string) => {
    deleteMutation.mutate(id);
  };


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
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-semibold">Templates List</h2>
            <Dialog open={newTemplateDialogOpen} onOpenChange={setNewTemplateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Template
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Template</DialogTitle>
                  <DialogDescription>
                    Create a new scenario template with name and optional notes/exclusions.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <label htmlFor="template-name" className="text-sm font-medium">
                      Template Name *
                    </label>
                    <Input
                      id="template-name"
                      value={newTemplateName}
                      onChange={(e) => setNewTemplateName(e.target.value)}
                      placeholder="Enter template name"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="template-notes" className="text-sm font-medium">
                      Notes / Exclusions
                    </label>
                    <p className="text-xs text-gray-500">
                      One bullet point per line. These will be stored as an array.
                    </p>
                    <Textarea
                      id="template-notes"
                      value={newTemplateNotes}
                      onChange={(e) => setNewTemplateNotes(e.target.value)}
                      placeholder="Enter notes or exclusions (one per line)"
                      rows={5}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setNewTemplateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateTemplate} disabled={createMutation.isPending}>
                    {createMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Create Template'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {templatesQuery.isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : templatesQuery.isError ? (
            <p className="text-red-500">Failed to load templates. Please try again.</p>
          ) : templatesQuery.data && templatesQuery.data.length === 0 ? (
            <p className="text-gray-500">No templates found. Create your first template above.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Name</TableHead>
                  <TableHead>Notes / Exclusions Preview</TableHead>
                  <TableHead className="w-[150px] text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templatesQuery.data?.map((template) => (
                  <TableRow key={template.id}>
                    {editingTemplateId === template.id ? (
                      <>
                        <TableCell>
                          <Input
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            placeholder="Template name"
                            className="w-full"
                          />
                        </TableCell>
                        <TableCell>
                          <Textarea
                            value={editNotes}
                            onChange={(e) => setEditNotes(e.target.value)}
                            placeholder="One bullet per line"
                            rows={3}
                            className="w-full"
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => saveEditing(template.id)}
                              disabled={updateMutation.isPending}
                            >
                              {updateMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Save className="h-4 w-4" />
                              )}
                            </Button>
                            <Button variant="ghost" size="sm" onClick={cancelEditing}>
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </>
                    ) : (
                      <>
                        <TableCell className="font-medium">{template.name}</TableCell>
                        <TableCell className="text-gray-500">
                          {template.notes_exclusions && template.notes_exclusions.length > 0
                            ? template.notes_exclusions.join(', ').substring(0, 80) +
                              (template.notes_exclusions.join(', ').length > 80 ? '...' : '')
                            : 'No notes/exclusions'}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => startEditing(template)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Dialog
                              open={deleteConfirmId === template.id}
                              onOpenChange={(open) => {
                                if (!open) setDeleteConfirmId(null);
                              }}
                            >
                              <DialogTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setDeleteConfirmId(template.id)}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>Delete Template</DialogTitle>
                                  <DialogDescription>
                                    Delete this template? This cannot be undone.
                                  </DialogDescription>
                                </DialogHeader>
                                <DialogFooter>
                                  <Button
                                    variant="outline"
                                    onClick={() => setDeleteConfirmId(null)}
                                  >
                                    Cancel
                                  </Button>
                                  <Button
                                    variant="destructive"
                                    onClick={() => confirmDelete(template.id)}
                                    disabled={deleteMutation.isPending}
                                  >
                                    {deleteMutation.isPending ? (
                                      <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Deleting...
                                      </>
                                    ) : (
                                      'Delete'
                                    )}
                                  </Button>
                                </DialogFooter>
                              </DialogContent>
                            </Dialog>
                          </div>
                        </TableCell>
                      </>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
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