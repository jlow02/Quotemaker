import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea"; // Assuming shadcn/ui textarea
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

// --- SIMULATED DATA AND API CALLS (Replace with actual backend integration) ---
/** @owner Gemini */
interface Template {
  id: string;
  name: string;
  description: string;
}

/** @owner Gemini */
let _SIMULATED_TEMPLATES_DATA: Template[] = [
  { id: 'temp_std_proj', name: 'Standard Project Quote', description: 'Template for typical project proposals.' },
  { id: 'temp_ent_deal', name: 'Enterprise Deal Template', description: 'Comprehensive template for large enterprise deals.' },
];

/**
 * @purpose Simulates a UI store for active sheet ID.
 * @owner Gemini
 */
const _SIMULATED_uiStore = {
  activeSheetId: 'sheet_abc_123', // Mock active sheet ID
};

/**
 * @purpose Simulates fetching a list of templates from an API.
 * @owner Gemini
 * @returns {Promise<Template[]>} A promise that resolves with the list of templates.
 */
const _SIMULATED_listTemplates = async (): Promise<Template[]> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return [..._SIMULATED_TEMPLATES_DATA];
};

/**
 * @purpose Simulates creating a new template via an API.
 * @owner Gemini
 * @param {Omit<Template, 'id'>} template - The template data to create.
 * @returns {Promise<Template>} A promise that resolves with the newly created template.
 */
const _SIMULATED_createTemplate = async (template: Omit<Template, 'id'>): Promise<Template> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  const newTemplate: Template = { ...template, id: `temp_${Date.now()}` };
  _SIMULATED_TEMPLATES_DATA.push(newTemplate);
  return newTemplate;
};

/**
 * @purpose Simulates deleting a template via an API.
 * @owner Gemini
 * @param {string} id - The ID of the template to delete.
 * @returns {Promise<{id: string}>} A promise that resolves with the ID of the deleted template.
 */
const _SIMULATED_deleteTemplate = async (id: string): Promise<{ id: string }> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  _SIMULATED_TEMPLATES_DATA = _SIMULATED_TEMPLATES_DATA.filter(t => t.id !== id);
  return { id };
};

/**
 * @purpose Simulates applying a template to a sheet via an API.
 * @owner Gemini
 * @param {string} templateId - The ID of the template to apply.
 * @param {string} sheetId - The ID of the sheet to apply the template to.
 * @returns {Promise<{templateId: string, sheetId: string, status: string}>} A promise that resolves with application status.
 */
const _SIMULATED_applyTemplate = async (templateId: string, sheetId: string): Promise<{ templateId: string, sheetId: string, status: string }> => {
  await new Promise(resolve => setTimeout(resolve, 800));
  console.log(`Template ${templateId} applied to sheet ${sheetId}.`);
  return { templateId, sheetId, status: `Template ${templateId} applied.` };
};
// --- END SIMULATED DATA ---

/** @owner Gemini */
interface TemplatesListProps {}

/**
 * @purpose Schema for creating a new template.
 * @owner Gemini
 */
const formSchema = z.object({
  name: z.string().min(2, { message: "Template name must be at least 2 characters." }),
  description: z.string().default(''),
});

/**
 * @purpose Manages scenario templates, allowing listing, creation, deletion, and application.
 * @param {TemplatesListProps} props - The properties for the component.
 * @owner Gemini
 * @returns {JSX.Element} The TemplatesList component.
 */
const TemplatesList: React.FC<TemplatesListProps> = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeSheetId = _SIMULATED_uiStore.activeSheetId;

  /**
   * @purpose Fetches the list of templates.
   * @owner Gemini
   */
  const fetchTemplates = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await _SIMULATED_listTemplates();
      setTemplates(data);
    } catch (err) {
      setError("Failed to fetch templates.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", description: "" },
  });

  /**
   * @purpose Handles the submission of the new template form.
   * @owner Gemini
   * @param {z.infer<typeof formSchema>} values - The form values.
   */
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_createTemplate(values);
      form.reset();
      await fetchTemplates(); // Refetch after successful creation
    } catch (err) {
      setError("Failed to create template.");
    } finally {
      setIsMutating(false);
    }
  };

  /**
   * @purpose Handles the deletion of a template.
   * @owner Gemini
   * @param {string} templateId - The ID of the template to delete.
   */
  const handleDeleteTemplate = async (templateId: string) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_deleteTemplate(templateId);
      await fetchTemplates(); // Refetch after successful deletion
    } catch (err) {
      setError("Failed to delete template.");
    } finally {
      setIsMutating(false);
    }
  };

  /**
   * @purpose Handles applying a template to the active sheet.
   * @owner Gemini
   * @param {string} templateId - The ID of the template to apply.
   */
  const handleApplyTemplate = async (templateId: string) => {
    if (!activeSheetId) {
      setError("No active sheet selected to apply template.");
      return;
    }
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_applyTemplate(templateId, activeSheetId);
      console.log(`Successfully applied template ${templateId} to ${activeSheetId}`);
    } catch (err) {
      setError("Failed to apply template.");
    } finally {
      setIsMutating(false);
    }
  };

  return (
    <div className="space-y-6 p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold">Scenario Templates</h2>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Create New Template</h3>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Template Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Q4 Forecast" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Brief description of the template" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isMutating}>
              {isMutating ? "Creating..." : "Create Template"}
            </Button>
          </form>
        </Form>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Existing Templates (Active Sheet: {activeSheetId || 'None'})</h3>
        {isLoading ? (
          <p>Loading templates...</p>
        ) : templates.length === 0 ? (
          <p>No templates found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {templates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell className="font-medium">{template.name}</TableCell>
                  <TableCell>{template.description}</TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleApplyTemplate(template.id)}
                      disabled={isMutating || !activeSheetId}
                    >
                      Apply
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteTemplate(template.id)}
                      disabled={isMutating}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default TemplatesList;