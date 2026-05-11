import type { LineItem } from '../../api/services';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { PlusCircleIcon, Trash2 } from 'lucide-react';

interface LineItemRowProps {
  item: LineItem;
  onDelete: (itemId: string) => void;
}

const LineItemRow = ({ item, onDelete }: LineItemRowProps): JSX.Element => (
  <TableRow key={item.id}>
    <TableCell className="font-medium max-w-[200px] truncate">{item.description}</TableCell>
    <TableCell className="w-[100px] text-right">{Number(item.qty)}</TableCell>
    <TableCell className="w-[150px] text-right">{Number(item.cost_rate).toFixed(2)}</TableCell>
    <TableCell className="w-[80px] text-center">{item.cost_currency}</TableCell>
    <TableCell className="w-[150px] text-right font-semibold">
      {(Number(item.qty) * Number(item.cost_rate)).toFixed(2)}
    </TableCell>
    <TableCell className="w-[100px] text-center">
      <Button
        variant="ghost"
        size="sm"
        className="text-red-500 hover:text-red-700 hover:bg-red-50 h-7 w-7 p-0"
        onClick={() => onDelete(item.id)}
        aria-label="Delete item"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </TableCell>
  </TableRow>
);

interface LineItemTableProps {
  scenarioId: string;
  lineItems: LineItem[];
  onAddLineItem: (scenarioId: string) => void;
  onDeleteLineItem: (itemId: string) => void;
}

/**
 * @purpose Displays a table of line items for a specific scenario, along with an option to add new items.
 * Renders individual LineItemRow components.
 * @param {LineItemTableProps} props - The props for the component.
 * @returns {JSX.Element} The rendered line item table component.
 * @owner Gemini
 */
export function LineItemTable({
  scenarioId,
  lineItems,
  onAddLineItem,
  onDeleteLineItem,
}: LineItemTableProps): JSX.Element {

  const handleAddLineItem = (): void => {
    onAddLineItem(scenarioId);
  };

  return (
    <div className="p-4 bg-background border rounded-lg shadow-sm">
      <Table className="min-w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="w-[35%]">Item</TableHead>
            <TableHead className="w-[10%] text-right">Qty</TableHead>
            <TableHead className="w-[15%] text-right">Unit Cost</TableHead>
            <TableHead className="w-[10%] text-center">Currency</TableHead>
            <TableHead className="w-[15%] text-right">Subtotal</TableHead>
            <TableHead className="w-[15%] text-center">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lineItems.length > 0 ? (
            lineItems.map((item) => <LineItemRow key={item.id} item={item} onDelete={onDeleteLineItem} />)
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                No line items added yet.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="mt-4 text-center">
        <Button onClick={handleAddLineItem} variant="outline" aria-label="Add new line item">
          <PlusCircleIcon className="mr-2 h-4 w-4" />
          Add Line Item
        </Button>
      </div>
    </div>
  );
}