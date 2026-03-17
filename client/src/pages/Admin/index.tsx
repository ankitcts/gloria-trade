import { useState, useMemo } from "react";
import {
  Box,
  Typography,
  Card,
  Tabs,
  Tab,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  Chip,
  IconButton,
  TextField,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  FormControl,
  InputLabel,
  Pagination,
  Menu,
  ListItemIcon,
  ListItemText,
  InputAdornment,
  CircularProgress,
  Alert,
  Autocomplete,
} from "@mui/material";
import {
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Group as GroupIcon,
  Security as SecurityIcon,
  PersonAdd as PersonAddIcon,
  PersonRemove as PersonRemoveIcon,
  Shield as ShieldIcon,
  SwapHoriz as SwapHorizIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import {
  useAdminUsers,
  useCreateUser,
  useUpdateUserRole,
  useUpdateUserStatus,
  useUpdateUserPermissions,
  useUpdateUserGroups,
  useDeleteUser,
  useGroups,
  useCreateGroup,
  useUpdateGroup,
  useDeleteGroup,
  useAddGroupMembers,
  useRemoveGroupMembers,
  usePermissions,
} from "@/api/hooks/useAdmin";
import type { User, UserGroup } from "@/types/auth";

// -- Constants --

const ROLES = ["admin", "trader", "analyst", "viewer"];
const STATUSES = ["active", "suspended", "pending_verification", "deactivated"];

const ROLE_COLORS: Record<string, "error" | "primary" | "info" | "default"> = {
  admin: "error",
  trader: "primary",
  analyst: "info",
  viewer: "default",
};

const STATUS_COLORS: Record<
  string,
  "success" | "error" | "warning" | "default"
> = {
  active: "success",
  suspended: "error",
  pending_verification: "warning",
  deactivated: "default",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Never";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatStatus(status: string): string {
  return status
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// ========== Users Tab ==========

function UsersTab() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const pageSize = 15;

  const { data: usersData, isLoading } = useAdminUsers(
    page,
    pageSize,
    roleFilter || undefined,
    statusFilter || undefined,
    search || undefined
  );
  const { data: groups } = useGroups();

  // Action menu state
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Dialog states
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [groupsDialogOpen, setGroupsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleOpenMenu = (
    event: React.MouseEvent<HTMLElement>,
    user: User
  ) => {
    setMenuAnchor(event.currentTarget);
    setSelectedUser(user);
  };

  const handleCloseMenu = () => {
    setMenuAnchor(null);
  };

  const openDialog = (
    type: "role" | "status" | "permissions" | "groups" | "delete"
  ) => {
    handleCloseMenu();
    switch (type) {
      case "role":
        setRoleDialogOpen(true);
        break;
      case "status":
        setStatusDialogOpen(true);
        break;
      case "permissions":
        setPermissionsDialogOpen(true);
        break;
      case "groups":
        setGroupsDialogOpen(true);
        break;
      case "delete":
        setDeleteDialogOpen(true);
        break;
    }
  };

  const totalPages = usersData
    ? Math.ceil(usersData.total / usersData.page_size)
    : 0;

  return (
    <Box>
      {/* Search and Filters */}
      <Box
        sx={{
          display: "flex",
          gap: 2,
          mb: 3,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <TextField
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          sx={{ minWidth: 280, flex: 1 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: "text.secondary" }} />
                </InputAdornment>
              ),
            },
          }}
        />
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Role</InputLabel>
          <Select
            value={roleFilter}
            label="Role"
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="">All Roles</MenuItem>
            {ROLES.map((role) => (
              <MenuItem key={role} value={role}>
                {role.charAt(0).toUpperCase() + role.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            {STATUSES.map((status) => (
              <MenuItem key={status} value={status}>
                {formatStatus(status)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => setCreateUserOpen(true)}
        >
          Create User
        </Button>
      </Box>

      {/* Users Table */}
      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Groups</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={32} />
                  </TableCell>
                </TableRow>
              ) : !usersData?.items?.length ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <Typography color="text.secondary">
                      No users found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                usersData.items.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {user.first_name} {user.last_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {user.email}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={
                          user.role.charAt(0).toUpperCase() + user.role.slice(1)
                        }
                        color={ROLE_COLORS[user.role] || "default"}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={formatStatus(user.account_status)}
                        color={
                          STATUS_COLORS[user.account_status] || "default"
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {user.group_ids?.length || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(user.last_login_at)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={(e) => handleOpenMenu(e, user)}
                      >
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {totalPages > 1 && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => setPage(value)}
              color="primary"
            />
          </Box>
        )}
      </Card>

      {/* Actions Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleCloseMenu}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
      >
        <MenuItem onClick={() => openDialog("role")}>
          <ListItemIcon>
            <ShieldIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Change Role</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => openDialog("status")}>
          <ListItemIcon>
            <SwapHorizIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Change Status</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => openDialog("permissions")}>
          <ListItemIcon>
            <SecurityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Manage Permissions</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => openDialog("groups")}>
          <ListItemIcon>
            <GroupIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Manage Groups</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => openDialog("delete")} sx={{ color: "error.main" }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete User</ListItemText>
        </MenuItem>
      </Menu>

      {/* Create User Dialog */}
      <CreateUserDialog
        open={createUserOpen}
        onClose={() => setCreateUserOpen(false)}
      />

      {/* Dialogs */}
      {selectedUser && (
        <>
          <RoleDialog
            open={roleDialogOpen}
            onClose={() => setRoleDialogOpen(false)}
            user={selectedUser}
          />
          <StatusDialog
            open={statusDialogOpen}
            onClose={() => setStatusDialogOpen(false)}
            user={selectedUser}
          />
          <UserPermissionsDialog
            open={permissionsDialogOpen}
            onClose={() => setPermissionsDialogOpen(false)}
            user={selectedUser}
          />
          <UserGroupsDialog
            open={groupsDialogOpen}
            onClose={() => setGroupsDialogOpen(false)}
            user={selectedUser}
            groups={groups || []}
          />
          <DeleteUserDialog
            open={deleteDialogOpen}
            onClose={() => setDeleteDialogOpen(false)}
            user={selectedUser}
          />
        </>
      )}
    </Box>
  );
}

// ========== User Dialogs ==========

function CreateUserDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState("viewer");
  const [status, setStatus] = useState("active");
  const [phone, setPhone] = useState("");
  const createUser = useCreateUser();

  const handleSave = async () => {
    await createUser.mutateAsync({
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      role,
      account_status: status,
      ...(phone && { phone }),
    });
    setEmail("");
    setPassword("");
    setFirstName("");
    setLastName("");
    setRole("viewer");
    setStatus("active");
    setPhone("");
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create User</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="First Name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              fullWidth
              required
            />
            <TextField
              label="Last Name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              fullWidth
              required
            />
          </Box>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            helperText="Minimum 8 characters"
          />
          <TextField
            label="Phone (optional)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            fullWidth
          />
          <Box sx={{ display: "flex", gap: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Role</InputLabel>
              <Select value={role} label="Role" onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => (
                  <MenuItem key={r} value={r}>
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
                {STATUSES.map((s) => (
                  <MenuItem key={s} value={s}>
                    {formatStatus(s)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        {createUser.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to create user. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={
            createUser.isPending ||
            !email.trim() ||
            !password.trim() ||
            password.length < 8 ||
            !firstName.trim() ||
            !lastName.trim()
          }
        >
          {createUser.isPending ? "Creating..." : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function RoleDialog({
  open,
  onClose,
  user,
}: {
  open: boolean;
  onClose: () => void;
  user: User;
}) {
  const [role, setRole] = useState(user.role);
  const updateRole = useUpdateUserRole();

  const handleSave = async () => {
    await updateRole.mutateAsync({ userId: user.id, role });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Change Role</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Changing role for {user.first_name} {user.last_name}
        </Typography>
        <FormControl fullWidth size="small">
          <InputLabel>Role</InputLabel>
          <Select value={role} label="Role" onChange={(e) => setRole(e.target.value)}>
            {ROLES.map((r) => (
              <MenuItem key={r} value={r}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {updateRole.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to update role. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updateRole.isPending || role === user.role}
        >
          {updateRole.isPending ? "Saving..." : "Save"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function StatusDialog({
  open,
  onClose,
  user,
}: {
  open: boolean;
  onClose: () => void;
  user: User;
}) {
  const [status, setStatus] = useState(user.account_status);
  const updateStatus = useUpdateUserStatus();

  const handleSave = async () => {
    await updateStatus.mutateAsync({ userId: user.id, status });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Change Status</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Changing status for {user.first_name} {user.last_name}
        </Typography>
        <FormControl fullWidth size="small">
          <InputLabel>Status</InputLabel>
          <Select
            value={status}
            label="Status"
            onChange={(e) => setStatus(e.target.value)}
          >
            {STATUSES.map((s) => (
              <MenuItem key={s} value={s}>
                {formatStatus(s)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {updateStatus.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to update status. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updateStatus.isPending || status === user.account_status}
        >
          {updateStatus.isPending ? "Saving..." : "Save"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function UserPermissionsDialog({
  open,
  onClose,
  user,
}: {
  open: boolean;
  onClose: () => void;
  user: User;
}) {
  const [selected, setSelected] = useState<string[]>(
    user.extra_permissions || []
  );
  const { data: allPermissions, isLoading } = usePermissions();
  const updatePermissions = useUpdateUserPermissions();

  const handleToggle = (perm: string) => {
    setSelected((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  const handleSave = async () => {
    await updatePermissions.mutateAsync({
      userId: user.id,
      permissions: selected,
    });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Manage Permissions</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Extra permissions for {user.first_name} {user.last_name}
        </Typography>
        {isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
              maxHeight: 400,
              overflowY: "auto",
            }}
          >
            {allPermissions?.map((perm) => (
              <FormControlLabel
                key={perm}
                control={
                  <Checkbox
                    checked={selected.includes(perm)}
                    onChange={() => handleToggle(perm)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                    {perm}
                  </Typography>
                }
              />
            ))}
            {!allPermissions?.length && (
              <Typography color="text.secondary" variant="body2">
                No permissions available
              </Typography>
            )}
          </Box>
        )}
        {updatePermissions.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to update permissions. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updatePermissions.isPending}
        >
          {updatePermissions.isPending ? "Saving..." : "Save"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function UserGroupsDialog({
  open,
  onClose,
  user,
  groups,
}: {
  open: boolean;
  onClose: () => void;
  user: User;
  groups: UserGroup[];
}) {
  const [selected, setSelected] = useState<string[]>(user.group_ids || []);
  const updateGroups = useUpdateUserGroups();

  const handleToggle = (groupId: string) => {
    setSelected((prev) =>
      prev.includes(groupId)
        ? prev.filter((g) => g !== groupId)
        : [...prev, groupId]
    );
  };

  const handleSave = async () => {
    await updateGroups.mutateAsync({ userId: user.id, groupIds: selected });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Manage Groups</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Group memberships for {user.first_name} {user.last_name}
        </Typography>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.5,
            maxHeight: 400,
            overflowY: "auto",
          }}
        >
          {groups.map((group) => (
            <FormControlLabel
              key={group.id}
              control={
                <Checkbox
                  checked={selected.includes(group.id)}
                  onChange={() => handleToggle(group.id)}
                  size="small"
                />
              }
              label={
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {group.name}
                  </Typography>
                  {group.description && (
                    <Typography variant="caption" color="text.secondary">
                      {group.description}
                    </Typography>
                  )}
                </Box>
              }
            />
          ))}
          {!groups.length && (
            <Typography color="text.secondary" variant="body2">
              No groups available
            </Typography>
          )}
        </Box>
        {updateGroups.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to update groups. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updateGroups.isPending}
        >
          {updateGroups.isPending ? "Saving..." : "Save"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function DeleteUserDialog({
  open,
  onClose,
  user,
}: {
  open: boolean;
  onClose: () => void;
  user: User;
}) {
  const deleteUser = useDeleteUser();

  const handleDelete = async () => {
    await deleteUser.mutateAsync(user.id);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Delete User</DialogTitle>
      <DialogContent>
        <Typography variant="body2">
          Are you sure you want to delete{" "}
          <strong>
            {user.first_name} {user.last_name}
          </strong>{" "}
          ({user.email})? This action cannot be undone.
        </Typography>
        {deleteUser.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to delete user. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleDelete}
          color="error"
          variant="contained"
          disabled={deleteUser.isPending}
        >
          {deleteUser.isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ========== Groups Tab ==========

function GroupsTab() {
  const { data: groups, isLoading } = useGroups();
  const { data: allPermissions } = usePermissions();
  const { data: usersData } = useAdminUsers(1, 1000);

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editGroup, setEditGroup] = useState<UserGroup | null>(null);
  const [membersGroup, setMembersGroup] = useState<UserGroup | null>(null);
  const [deleteGroup, setDeleteGroup] = useState<UserGroup | null>(null);

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          mb: 3,
        }}
      >
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Group
        </Button>
      </Box>

      {/* Groups Table */}
      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Permissions</TableCell>
                <TableCell>Members</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={32} />
                  </TableCell>
                </TableRow>
              ) : !groups?.length ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <Typography color="text.secondary">
                      No groups found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                groups.map((group) => (
                  <TableRow key={group.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {group.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          maxWidth: 300,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {group.description || "--"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {group.permissions?.length || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {group.member_count}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(group.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => setEditGroup(group)}
                        title="Edit"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => setMembersGroup(group)}
                        title="Manage Members"
                      >
                        <GroupIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => setDeleteGroup(group)}
                        title="Delete"
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Create Group Dialog */}
      <GroupFormDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        allPermissions={allPermissions || []}
      />

      {/* Edit Group Dialog */}
      {editGroup && (
        <GroupFormDialog
          open={Boolean(editGroup)}
          onClose={() => setEditGroup(null)}
          group={editGroup}
          allPermissions={allPermissions || []}
        />
      )}

      {/* Members Dialog */}
      {membersGroup && (
        <GroupMembersDialog
          open={Boolean(membersGroup)}
          onClose={() => setMembersGroup(null)}
          group={membersGroup}
          allUsers={usersData?.items || []}
        />
      )}

      {/* Delete Dialog */}
      {deleteGroup && (
        <DeleteGroupDialog
          open={Boolean(deleteGroup)}
          onClose={() => setDeleteGroup(null)}
          group={deleteGroup}
        />
      )}
    </Box>
  );
}

// ========== Group Dialogs ==========

function GroupFormDialog({
  open,
  onClose,
  group,
  allPermissions,
}: {
  open: boolean;
  onClose: () => void;
  group?: UserGroup;
  allPermissions: string[];
}) {
  const [name, setName] = useState(group?.name || "");
  const [description, setDescription] = useState(group?.description || "");
  const [permissions, setPermissions] = useState<string[]>(
    group?.permissions || []
  );

  const createGroup = useCreateGroup();
  const updateGroup = useUpdateGroup();

  const isEdit = Boolean(group);
  const mutation = isEdit ? updateGroup : createGroup;

  const handleTogglePermission = (perm: string) => {
    setPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  const handleSave = async () => {
    if (isEdit && group) {
      await updateGroup.mutateAsync({
        groupId: group.id,
        data: { name, description: description || null, permissions },
      });
    } else {
      await createGroup.mutateAsync({
        name,
        description: description || null,
        permissions,
      });
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? "Edit Group" : "Create Group"}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          <TextField
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            rows={2}
          />
          <Typography variant="subtitle2" sx={{ mt: 1 }}>
            Permissions
          </Typography>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
              maxHeight: 300,
              overflowY: "auto",
              pl: 1,
            }}
          >
            {allPermissions.map((perm) => (
              <FormControlLabel
                key={perm}
                control={
                  <Checkbox
                    checked={permissions.includes(perm)}
                    onChange={() => handleTogglePermission(perm)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                    {perm}
                  </Typography>
                }
              />
            ))}
            {!allPermissions.length && (
              <Typography color="text.secondary" variant="body2">
                No permissions available
              </Typography>
            )}
          </Box>
        </Box>
        {mutation.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to {isEdit ? "update" : "create"} group. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={mutation.isPending || !name.trim()}
        >
          {mutation.isPending ? "Saving..." : isEdit ? "Update" : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function GroupMembersDialog({
  open,
  onClose,
  group,
  allUsers,
}: {
  open: boolean;
  onClose: () => void;
  group: UserGroup;
  allUsers: User[];
}) {
  const addMembers = useAddGroupMembers();
  const removeMembers = useRemoveGroupMembers();
  const [addUserValue, setAddUserValue] = useState<User | null>(null);

  const currentMembers = useMemo(
    () => allUsers.filter((u) => group.member_ids?.includes(u.id)),
    [allUsers, group.member_ids]
  );

  const availableUsers = useMemo(
    () => allUsers.filter((u) => !group.member_ids?.includes(u.id)),
    [allUsers, group.member_ids]
  );

  const handleAddMember = async () => {
    if (!addUserValue) return;
    await addMembers.mutateAsync({
      groupId: group.id,
      memberIds: [addUserValue.id],
    });
    setAddUserValue(null);
  };

  const handleRemoveMember = async (userId: string) => {
    await removeMembers.mutateAsync({
      groupId: group.id,
      memberIds: [userId],
    });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Manage Members - {group.name}</DialogTitle>
      <DialogContent>
        {/* Add member */}
        <Box sx={{ display: "flex", gap: 1, mb: 3, pt: 1 }}>
          <Autocomplete
            value={addUserValue}
            onChange={(_, newValue) => setAddUserValue(newValue)}
            options={availableUsers}
            getOptionLabel={(u) =>
              `${u.first_name} ${u.last_name} (${u.email})`
            }
            renderInput={(params) => (
              <TextField {...params} label="Add member" size="small" />
            )}
            sx={{ flex: 1 }}
            size="small"
          />
          <Button
            variant="contained"
            onClick={handleAddMember}
            disabled={!addUserValue || addMembers.isPending}
            startIcon={<PersonAddIcon />}
            size="small"
          >
            Add
          </Button>
        </Box>

        {/* Current members list */}
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Current Members ({currentMembers.length})
        </Typography>
        <Box
          sx={{
            maxHeight: 350,
            overflowY: "auto",
          }}
        >
          {currentMembers.length === 0 ? (
            <Typography color="text.secondary" variant="body2" sx={{ py: 2 }}>
              No members in this group
            </Typography>
          ) : (
            currentMembers.map((member) => (
              <Box
                key={member.id}
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  py: 1,
                  px: 1,
                  borderRadius: 1,
                  "&:hover": {
                    backgroundColor: "action.hover",
                  },
                }}
              >
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {member.first_name} {member.last_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {member.email}
                  </Typography>
                </Box>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleRemoveMember(member.id)}
                  disabled={removeMembers.isPending}
                  title="Remove member"
                >
                  <PersonRemoveIcon fontSize="small" />
                </IconButton>
              </Box>
            ))
          )}
        </Box>

        {(addMembers.isError || removeMembers.isError) && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to update members. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

function DeleteGroupDialog({
  open,
  onClose,
  group,
}: {
  open: boolean;
  onClose: () => void;
  group: UserGroup;
}) {
  const deleteGroupMutation = useDeleteGroup();

  const handleDelete = async () => {
    await deleteGroupMutation.mutateAsync(group.id);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Delete Group</DialogTitle>
      <DialogContent>
        <Typography variant="body2">
          Are you sure you want to delete the group{" "}
          <strong>{group.name}</strong>? This will remove all member
          associations. This action cannot be undone.
        </Typography>
        {deleteGroupMutation.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to delete group. Please try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleDelete}
          color="error"
          variant="contained"
          disabled={deleteGroupMutation.isPending}
        >
          {deleteGroupMutation.isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ========== Admin Page ==========

export default function Admin() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Admin
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
          Manage users, groups, roles, and permissions
        </Typography>
      </Box>

      {/* Tabs */}
      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
          mb: 3,
        }}
      >
        <Tabs
          value={tab}
          onChange={(_, newValue) => setTab(newValue)}
          sx={{
            px: 2,
            "& .MuiTab-root": {
              textTransform: "none",
              fontWeight: 600,
            },
          }}
        >
          <Tab label="Users" />
          <Tab label="Groups" />
        </Tabs>
      </Card>

      {/* Tab Panels */}
      {tab === 0 && <UsersTab />}
      {tab === 1 && <GroupsTab />}
    </Box>
  );
}
