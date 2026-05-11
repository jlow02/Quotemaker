import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

// --- SIMULATED DATA AND API CALLS (Replace with actual backend integration) ---
/** @owner Gemini */
interface Organisation {
  id: string;
  name: string;
}

/** @owner Gemini */
let _SIMULATED_ORGANISATIONS_DATA: Organisation[] = [
  { id: 'org_nxtn', name: 'NEXTAN Corp' },
  { id: 'org_glbl', name: 'Global Solutions Inc.' },
];

/**
 * @purpose Simulates fetching a list of organisations from an API.
 * @owner Gemini
 * @returns {Promise<Organisation[]>} A promise that resolves with the list of organisations.
 */
const _SIMULATED_listOrganisations = async (): Promise<Organisation[]> => {
  await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
  return [..._SIMULATED_ORGANISATIONS_DATA];
};

/**
 * @purpose Simulates creating a new organisation via an API.
 * @owner Gemini
 * @param {string} name - The name of the new organisation.
 * @returns {Promise<Organisation>} A promise that resolves with the newly created organisation.
 */
const _SIMULATED_createOrganisation = async (name: string): Promise<Organisation> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  const newOrg: Organisation = { id: `org_${Date.now()}`, name };
  _SIMULATED_ORGANISATIONS_DATA.push(newOrg);
  return newOrg;
};

/**
 * @purpose Simulates deleting an organisation via an API.
 * @owner Gemini
 * @param {string} id - The ID of the organisation to delete.
 * @returns {Promise<{id: string}>} A promise that resolves with the ID of the deleted organisation.
 */
const _SIMULATED_deleteOrganisation = async (id: string): Promise<{ id: string }> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  _SIMULATED_ORGANISATIONS_DATA = _SIMULATED_ORGANISATIONS_DATA.filter(org => org.id !== id);
  return { id };
};
// --- END SIMULATED DATA ---

/** @owner Gemini */
interface OrgManagerProps {}

/**
 * @purpose Schema for creating a new organisation.
 * @owner Gemini
 */
const formSchema = z.object({
  name: z.string().min(2, { message: "Organisation name must be at least 2 characters." }),
});

/**
 * @purpose Manages organisations, allowing listing, creation, and deletion.
 * @param {OrgManagerProps} props - The properties for the component.
 * @owner Gemini
 * @returns {JSX.Element} The OrgManager component.
 */
const OrgManager: React.FC<OrgManagerProps> = () => {
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * @purpose Fetches the list of organisations.
   * @owner Gemini
   */
  const fetchOrganisations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await _SIMULATED_listOrganisations();
      setOrganisations(data);
    } catch (err) {
      setError("Failed to fetch organisations.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrganisations();
  }, [fetchOrganisations]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "" },
  });

  /**
   * @purpose Handles the submission of the new organisation form.
   * @owner Gemini
   * @param {z.infer<typeof formSchema>} values - The form values.
   */
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_createOrganisation(values.name);
      form.reset();
      await fetchOrganisations(); // Refetch after successful creation
    } catch (err) {
      setError("Failed to create organisation.");
    } finally {
      setIsMutating(false);
    }
  };

  /**
   * @purpose Handles the deletion of an organisation.
   * @owner Gemini
   * @param {string} orgId - The ID of the organisation to delete.
   */
  const handleDeleteOrg = async (orgId: string) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_deleteOrganisation(orgId);
      await fetchOrganisations(); // Refetch after successful deletion
    } catch (err) {
      setError("Failed to delete organisation.");
    } finally {
      setIsMutating(false);
    }
  };

  return (
    <div className="space-y-6 p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold">Organisation Manager</h2>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Create New Organisation</h3>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Organisation Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Acme Solutions" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isMutating}>
              {isMutating ? "Creating..." : "Create Organisation"}
            </Button>
          </form>
        </Form>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Existing Organisations</h3>
        {isLoading ? (
          <p>Loading organisations...</p>
        ) : organisations.length === 0 ? (
          <p>No organisations found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {organisations.map((org) => (
                <TableRow key={org.id}>
                  <TableCell className="font-medium">{org.name}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteOrg(org.id)}
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

export default OrgManager;