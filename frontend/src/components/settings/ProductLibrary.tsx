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
interface Product {
  id: string;
  name: string;
  default_cost: number;
  currency: string;
}

/** @owner Gemini */
let _SIMULATED_PRODUCTS_DATA: Product[] = [
  { id: 'prod_sw_lic', name: 'Software License', default_cost: 1500, currency: 'USD' },
  { id: 'prod_impl_srv', name: 'Implementation Service', default_cost: 800, currency: 'EUR' },
];

/**
 * @purpose Simulates fetching a list of products from an API.
 * @owner Gemini
 * @returns {Promise<Product[]>} A promise that resolves with the list of products.
 */
const _SIMULATED_listProducts = async (): Promise<Product[]> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return [..._SIMULATED_PRODUCTS_DATA];
};

/**
 * @purpose Simulates creating a new product via an API.
 * @owner Gemini
 * @param {Omit<Product, 'id'>} product - The product data to create.
 * @returns {Promise<Product>} A promise that resolves with the newly created product.
 */
const _SIMULATED_createProduct = async (product: Omit<Product, 'id'>): Promise<Product> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  const newProduct: Product = { ...product, id: `prod_${Date.now()}` };
  _SIMULATED_PRODUCTS_DATA.push(newProduct);
  return newProduct;
};

/**
 * @purpose Simulates deleting a product via an API.
 * @owner Gemini
 * @param {string} id - The ID of the product to delete.
 * @returns {Promise<{id: string}>} A promise that resolves with the ID of the deleted product.
 */
const _SIMULATED_deleteProduct = async (id: string): Promise<{ id: string }> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  _SIMULATED_PRODUCTS_DATA = _SIMULATED_PRODUCTS_DATA.filter(p => p.id !== id);
  return { id };
};
// --- END SIMULATED DATA ---

/** @owner Gemini */
interface ProductLibraryProps {}

/**
 * @purpose Schema for creating a new product.
 * @owner Gemini
 */
const formSchema = z.object({
  name: z.string().min(2, { message: "Product name must be at least 2 characters." }),
  default_cost: z.coerce.number().min(0, { message: "Cost must be a positive number." }),
  currency: z.string().min(2, { message: "Currency must be specified (e.g., USD, EUR)." }),
});

/**
 * @purpose Manages the product library, allowing listing, creation, and deletion of products.
 * @param {ProductLibraryProps} props - The properties for the component.
 * @owner Gemini
 * @returns {JSX.Element} The ProductLibrary component.
 */
const ProductLibrary: React.FC<ProductLibraryProps> = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * @purpose Fetches the list of products.
   * @owner Gemini
   */
  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await _SIMULATED_listProducts();
      setProducts(data);
    } catch (err) {
      setError("Failed to fetch products.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", default_cost: 0, currency: "" },
  });

  /**
   * @purpose Handles the submission of the new product form.
   * @owner Gemini
   * @param {z.infer<typeof formSchema>} values - The form values.
   */
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_createProduct(values);
      form.reset();
      await fetchProducts(); // Refetch after successful creation
    } catch (err) {
      setError("Failed to create product.");
    } finally {
      setIsMutating(false);
    }
  };

  /**
   * @purpose Handles the deletion of a product.
   * @owner Gemini
   * @param {string} productId - The ID of the product to delete.
   */
  const handleDeleteProduct = async (productId: string) => {
    setIsMutating(true);
    setError(null);
    try {
      await _SIMULATED_deleteProduct(productId);
      await fetchProducts(); // Refetch after successful deletion
    } catch (err) {
      setError("Failed to delete product.");
    } finally {
      setIsMutating(false);
    }
  };

  return (
    <div className="space-y-6 p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold">Product Library</h2>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Add New Product</h3>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Product Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Enterprise Software" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="default_cost"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Default Cost</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Currency</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., USD" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isMutating}>
              {isMutating ? "Adding..." : "Add Product"}
            </Button>
          </form>
        </Form>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>

      <div className="border rounded-lg p-4 bg-white">
        <h3 className="text-xl font-semibold mb-4">Existing Products</h3>
        {isLoading ? (
          <p>Loading products...</p>
        ) : products.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Cost</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((product) => (
                <TableRow key={product.id}>
                  <TableCell className="font-medium">{product.name}</TableCell>
                  <TableCell>{product.default_cost.toFixed(2)}</TableCell>
                  <TableCell>{product.currency}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteProduct(product.id)}
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

export default ProductLibrary;