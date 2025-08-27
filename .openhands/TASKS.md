# Task List

1. ✅ Remove font-mono from branch item
Remove the font-mono class from branch name display
2. ✅ Analyze branch and repo item components for commonality
Both components are nearly identical - same structure, styling, just different props and display text
3. ✅ Create generic dropdown item component
Created generic DropdownItem component that accepts item type, display text function, and key function
4. ✅ Update branch dropdown to use generic item
Updated BranchDropdownMenu to use DropdownItem with branch-specific functions
5. ✅ Update repository dropdown to use generic item
Updated DropdownMenu to use DropdownItem with repository-specific functions
6. ✅ Test the generic component implementation
Build passes successfully, old components removed, exports cleaned up
