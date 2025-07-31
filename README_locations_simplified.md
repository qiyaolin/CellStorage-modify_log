# Storage Location Management - Simplified Interface

## Overview
This is a simplified version of the storage location management interface, designed specifically for managing a three-tier storage structure: Tower → Drawer → Box.

## Features

### Core Functionality
- **Three-tier Structure**: Manage Tower, Drawer, and Box hierarchy
- **Direct Operations**: Add and delete operations directly from tree nodes
- **Visual Hierarchy**: Clear tree structure with expandable/collapsible nodes
- **Capacity Tracking**: Visual capacity indicators for Drawers and Boxes
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### User Interface
- **Left Panel**: Tree structure showing all storage locations
- **Right Panel**: Details view for selected locations
- **Modal Forms**: Add/edit location information
- **Confirmation Dialogs**: Safe deletion with warnings

### Keyboard Shortcuts
- `Ctrl/Cmd + N`: Add new Tower
- `Delete`: Delete selected location
- `Escape`: Close open modals

## File Structure

```
app/
├── templates/inventory/
│   ├── locations_simplified.html          # Main template
│   └── partials/
│       └── location_node_simplified.html  # Tree node template
├── static/
│   ├── css/
│   │   └── locations-simplified.css       # Simplified styles
│   └── js/
│       └── locations-simplified.js        # Interactive functionality
```

## Usage Instructions

### Adding Locations
1. **Add Tower**: Click "Add Tower" button in the header
2. **Add Drawer**: Click the "+" button next to any Tower
3. **Add Box**: Click the "+" button next to any Drawer

### Managing Locations
1. **View Details**: Click on any location name to see details in the right panel
2. **Edit Location**: Click the "Edit" button in the details panel or tree node
3. **Delete Location**: Click the "Delete" button (with confirmation)

### Navigation
- **Expand/Collapse**: Click the chevron icon next to parent nodes
- **Tree State**: Expansion state is remembered between sessions
- **Selection**: Selected location is highlighted with blue border

## Technical Details

### Dependencies
- Bootstrap 5.x (for modals and basic styling)
- Bootstrap Icons (for UI icons)
- Modern browser with ES6+ support

### Browser Support
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Responsive Breakpoints
- **Desktop**: > 768px (two-column layout)
- **Tablet**: 481px - 768px (stacked layout)
- **Mobile**: ≤ 480px (single column with optimized controls)

## Customization

### Colors
The interface uses a consistent color scheme:
- Primary: #007bff (blue)
- Success: #28a745 (green)
- Warning: #ffc107 (yellow)
- Danger: #dc3545 (red)

### Icons
- Tower: Building icon (bi-building)
- Drawer: Inbox icon (bi-inbox)
- Box: Box icon (bi-box)

### Capacity Indicators
- Normal: < 60% (green)
- Warning: 60-80% (yellow)
- Critical: 80-100% (red)

## Integration Notes

This simplified interface is designed to work with the existing Flask backend without requiring changes to the server-side code. It expects the same API endpoints as the original interface:

- `GET /inventory/locations/{id}/details` - Get location details
- `POST /inventory/locations/add` - Add new location
- `POST /inventory/locations/{id}/edit` - Edit existing location
- `POST /inventory/locations/{id}/delete` - Delete location

## Performance Considerations

- Tree state is stored in localStorage for persistence
- Animations use CSS transitions for smooth performance
- Form validation happens client-side before submission
- Loading states provide user feedback during operations

## Accessibility

- Keyboard navigation support
- ARIA labels for screen readers
- High contrast color scheme
- Focus indicators for all interactive elements