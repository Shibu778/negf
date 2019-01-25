import copy
import numpy as np
import matplotlib.pyplot as plt


def mat_left_div(mat_a, mat_b):
    mat_a = np.asmatrix(mat_a)
    mat_b = np.asmatrix(mat_b)

    ans, resid, rank, s = np.linalg.lstsq(mat_a, mat_b, rcond=-1)

    return ans


def mat_mul(list_of_matrices):
    num_of_mat = len(list_of_matrices)

    unity = np.eye(list_of_matrices[num_of_mat - 1].shape[0])

    for j, item in enumerate(list_of_matrices):
        list_of_matrices[j] = np.matrix(item)

    for j in range(9, -1, -1):
        unity = list_of_matrices[j] * unity

    return unity


def recursive_gf(energy, mat_l_list, mat_d_list, mat_u_list, s_in=0, s_out=0):
    """
    The recursive Green's function algorithm is taken from
    M. P. Anantram, M. S. Lundstrom and D. E. Nikonov, Proceedings of the IEEE, 96, 1511 - 1550 (2008)
    DOI: 10.1109/JPROC.2008.927355


    :param energy:                     energy
    :param mat_d_list:                 list of diagonal blocks
    :param mat_u_list:                 list of upper-diagonal blocks
    :param mat_l_list:                 list of lower-diagonal blocks

    :return grd, grl, gru, gr_left:    retarded Green's
                                       function: block-diagonal,
                                                 lower block-diagonal,
                                                 upper block-diagonal,
                                                 left-connected
    """
    # -------------------------------------------------------------------
    # ---------- convert input arrays to matrix data type ---------------
    # -------------------------------------------------------------------

    for jj, item in enumerate(mat_d_list):
        mat_d_list[jj] = np.asmatrix(item)
        mat_d_list[jj] = mat_d_list[jj] - np.diag(energy * np.ones(mat_d_list[jj].shape[0]))

        if jj < len(mat_d_list) - 1:
            mat_u_list[jj] = np.asmatrix(mat_u_list[jj])
            mat_l_list[jj] = np.asmatrix(mat_l_list[jj])

    # computes matrix sizes
    num_of_matrices = len(mat_d_list)  # Number of diagonal blocks.
    mat_shapes = [item.shape for item in mat_d_list]  # This gives the sizes of the diagonal matrices.

    # -------------------------------------------------------------------
    # -------------- compute retarded Green's function ------------------
    # -------------------------------------------------------------------

    # allocate empty lists of certain lengths
    gr_left = [None for _ in range(num_of_matrices)]
    gr_left[0] = mat_left_div(-mat_d_list[0], np.eye(mat_shapes[0][0]))  # Initialising the retarded left connected.

    for q in range(num_of_matrices - 1):  # Recursive algorithm (B2)
        gr_left[q + 1] = mat_left_div((-mat_d_list[q + 1] - mat_l_list[q] * gr_left[q] * mat_u_list[q]),
                                      np.eye(mat_shapes[q + 1][0]))      # The left connected recursion.
    # -------------------------------------------------------------------

    grl = [None for _ in range(num_of_matrices-1)]
    gru = [None for _ in range(num_of_matrices-1)]
    grd = copy.copy(gr_left)                                       # Our glorious benefactor.

    for q in range(num_of_matrices - 2, -1, -1):                   # Recursive algorithm
        grl[q] = grd[q + 1] * mat_l_list[q] * gr_left[q]           # (B5) We get the off-diagonal blocks for free.
        gru[q] = gr_left[q] * mat_u_list[q] * grd[q + 1]           # (B6) because we need .Tthem.T for the next calc:
        grd[q] = gr_left[q] + gr_left[q] * mat_u_list[q] * grl[q]  # (B4) I suppose I could also use the lower.

    # -------------------------------------------------------------------
    # ------ compute the electron correlation function if needed --------
    # -------------------------------------------------------------------
    if isinstance(s_in, list):

        gin_left = [None for _ in range(num_of_matrices)]
        gin_left[0] = gr_left[0] * s_in[0] * np.conj(gr_left[0])

        for q in range(num_of_matrices - 1):
            sla2 = mat_l_list[q] * gin_left[q] * np.conj(mat_u_list[q])
            prom = s_in[q + 1] + sla2
            gin_left[q + 1] = np.real(gr_left[q + 1] * prom * np.conj(gr_left[q + 1]))

        # ---------------------------------------------------------------

        gnl = [None for _ in range(num_of_matrices - 1)]
        gnu = [None for _ in range(num_of_matrices - 1)]
        gnd = copy.copy(gin_left)

        for q in range(num_of_matrices - 2, -1, -1):               # Recursive algorithm
            gnl[q] = grd[q + 1] * mat_l_list[q] * gin_left[q] + gnd[q + 1] * np.conj(mat_l_list[q]) * np.conj(gr_left[q])
            gnd[q] = np.real(gin_left[q] +
                             gr_left[q] * mat_u_list[q] * gnd[q + 1] * np.conj(mat_l_list[q]) * np.conj(gr_left[q]) +
                             (gin_left[q] * np.conj(mat_u_list[q]) * np.conj(grl[q]) + gru[q] * mat_l_list[q] * gin_left[q]))

            gnu[q] = np.conj(gnl[q])

    # -------------------------------------------------------------------
    # -------- compute the hole correlation function if needed ----------
    # -------------------------------------------------------------------
    if isinstance(s_out, list):

        gip_left = [None for _ in range(num_of_matrices)]
        gip_left[0] = gr_left[0] * s_out[0] * gr_left[0].H

        for q in range(num_of_matrices - 1):
            sla2 = mat_l_list[q] * gip_left[q] * mat_u_list[q].H
            prom = s_out[q + 1] + sla2
            gip_left[q + 1] = np.real(gr_left[q + 1] * prom * gr_left[q + 1].H)

        # ---------------------------------------------------------------

        gpl = [None for _ in range(num_of_matrices - 1)]
        gpu = [None for _ in range(num_of_matrices - 1)]
        gpd = copy.copy(gip_left)

        for q in range(num_of_matrices - 2, -1, -1):               # Recursive algorithm
            gpl[q] = grd[q + 1] * mat_l_list[q] * gip_left[q] + gpd[q + 1] * mat_l_list[q].H * gr_left[q].H
            gpd[q] = np.real(gip_left[q] +
                             gr_left[q] * mat_u_list[q] * gpd[q + 1] * mat_l_list[q].H * gr_left[q].H +
                             (gip_left[q] * mat_u_list[q].H * grl[q].H + gru[q] * mat_l_list[q] * gip_left[q]))

            gpu[0] = gpl[0].H

    # -------------------------------------------------------------------
    # -- remove energy from the main diagonal of th Hamiltonian matrix --
    # -------------------------------------------------------------------

    for jj, item in enumerate(mat_d_list):
        mat_d_list[jj] = mat_d_list[jj] + np.diag(energy * np.ones(mat_d_list[jj].shape[0]))

    # -------------------------------------------------------------------
    # ---- choose a proper output depending on the list of arguments ----
    # -------------------------------------------------------------------

    if not isinstance(s_in, list) and not isinstance(s_out, list):
        return grd, grl, gru, gr_left

    elif isinstance(s_in, list) and not isinstance(s_out, list):
        return grd, grl, gru, gr_left, \
               gnd, gnl, gnu, gin_left

    elif not isinstance(s_in, list) and isinstance(s_out, list):
        return grd, grl, gru, gr_left, \
               gpd, gpl, gpu, gip_left

    else:
        return grd, grl, gru, gr_left, \
               gnd, gnl, gnu, gin_left, \
               gpd, gpl, gpu, gip_left
